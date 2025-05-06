from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('COMPLETED', 'Completed'),
    ('FAILED', 'Failed'),
]

class User(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    subscription_override = models.BooleanField(default=False, help_text="Allow admin to manually override subscription status")
    subscription_end_date = models.DateTimeField(null=True, blank=True, help_text="Manual subscription end date set by admin")
    max_emails_override = models.IntegerField(null=True, blank=True, help_text="Override monthly email limit")
    notes = models.TextField(blank=True, null=True, help_text="Admin notes about subscription status")

    @classmethod
    def get_profile(cls, user):
        """Get or create user profile"""
        profile, created = cls.objects.get_or_create(user=user)
        return profile

    @property
    def has_active_subscription(self):
        if self.subscription_override:
            return self.subscription_end_date and self.subscription_end_date > timezone.now()
        return Subscription.objects.filter(
            user=self.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).exists()

    @property
    def max_monthly_emails(self):
        if self.subscription_override and self.max_emails_override:
            return self.max_emails_override
        subscription = Subscription.objects.filter(
            user=self.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).first()
        return subscription.plan.max_emails_per_month if subscription else 0

    def __str__(self):
        status = "Manual Override" if self.subscription_override else "Regular Subscription"
        return f'Profile of {self.user.username} ({status})'

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Payment_account(models.Model):
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=10, null=True, blank=True)
    account_holder_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f'Payment Account of {self.account_holder_name}'

    class Meta:
        verbose_name = 'Payment Account'
        verbose_name_plural = 'Payment Accounts'


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_emails_per_month = models.IntegerField(default=100)
    duration_days = models.IntegerField(default=30)

    class Meta:
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} Plan - ₦{self.price}"


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new subscription
            self.start_date = timezone.now()
        if not self.end_date:
            self.end_date = (self.start_date or timezone.now()) + timezone.timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def is_valid(self):
        return self.is_active and self.end_date > timezone.now()

    def get_monthly_usage(self):
        from core.models import Campaign
        return Campaign.objects.filter(
            user=self.user,
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).count()

    def has_reached_limit(self):
        return self.get_monthly_usage() >= self.plan.max_emails_per_month

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.user.username}'s subscription enabled"


class Deposit(models.Model):
    deposit_id = ShortUUIDField(unique=True, max_length=8, length=5, prefix='dp', alphabet='0123456789')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_account = models.ForeignKey(Payment_account, on_delete=models.CASCADE, null=True, blank=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
   # receipt = models.ImageField(upload_to='deposits/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'])], help_text="Upload payment receipt")
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    @property
    def amount(self):
        return self.subscription_plan.price

    @property
    def has_proof(self):
        return bool(self.receipt)


    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'

    def __str__(self):
        return f'{self.user.username} -  subscription payment'


class Transactions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    @property
    def amount(self):
        return self.subscription.plan.price

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

    def __str__(self):
        return f'{self.user.username} - subscription'


@receiver(pre_save, sender=Deposit)
def create_subscription_on_deposit(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = Deposit.objects.get(id=instance.id)
            # Only proceed if status is changing from non-COMPLETED to COMPLETED
            if old_instance.status != 'COMPLETED' and instance.status == 'COMPLETED':
                # Check if a transaction already exists for this deposit
                existing_transaction = Transactions.objects.filter(
                    user=instance.user,
                    subscription__plan=instance.subscription_plan,
                    created_at__date=instance.created_at.date()
                ).exists()

                if not existing_transaction:
                    # Create or extend subscription
                    subscription = Subscription.objects.create(
                        user=instance.user,
                        plan=instance.subscription_plan
                    )
                    # Create transaction record
                    Transactions.objects.create(
                        user=instance.user,
                        subscription=subscription,
                        status='COMPLETED'
                    )
        except Deposit.DoesNotExist:
            pass
