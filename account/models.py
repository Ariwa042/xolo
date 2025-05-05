from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator

STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('COMPLETED', 'Completed'),
    ('FAILED', 'Failed'),
]

TYPE_CHOICES = [
    ('DEPOSIT', 'Deposit'),
    ('SPENT', 'Spent'),
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
    xp_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Profile of {self.user.username}'

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


class Deposit(models.Model):
    deposit_id = ShortUUIDField(unique=True, max_length=8, length=5, prefix='dp', alphabet='0123456789')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_account = models.ForeignKey(Payment_account, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f'{self.user.username} deposited {self.amount}'

    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'


class Spend(models.Model):
    spend_id = ShortUUIDField(unique=True, max_length=8, length=5, alphabet='0123456789', prefix='sp')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f'{self.user.username} spent {self.amount}'

    class Meta:
        verbose_name = 'Spend'
        verbose_name_plural = 'Spend'


class Transactions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} {self.type} {self.amount}'

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'


@receiver(pre_save, sender=Deposit)
def update_balance_on_deposit(sender, instance, **kwargs):
    if instance.id:
        old_instance = Deposit.objects.get(id=instance.id)
        if old_instance.status != 'COMPLETED' and instance.status == 'COMPLETED':
            user_profile = UserProfile.objects.get(user=instance.user)
            user_profile.xp_balance += instance.amount
            user_profile.save()
            # Create a corresponding transaction
            Transactions.objects.create(
                user=instance.user,
                type='DEPOSIT',
                amount=instance.amount,
                status='COMPLETED',
                created_at=timezone.now()
            )


@receiver(pre_save, sender=Spend)
def update_balance_on_spend(sender, instance, **kwargs):
    if instance.id:
        old_instance = Spend.objects.get(id=instance.id)
        if old_instance.status != 'COMPLETED' and instance.status == 'COMPLETED':
            user_profile = UserProfile.objects.get(user=instance.user)
            if user_profile.xp_balance >= instance.amount:
                user_profile.xp_balance -= instance.amount
                user_profile.save()
                # Create a corresponding transaction
                Transactions.objects.create(
                    user=instance.user,
                    type='SPENT',
                    amount=instance.amount,
                    status='COMPLETED',
                    created_at=timezone.now()
                )
            else:
                raise ValueError("Insufficient balance to process Spend on anything")


@receiver(pre_save, sender=Deposit)
@receiver(pre_save, sender=Spend)
def update_transaction_status(sender, instance, **kwargs):
    """ Update transaction when deposit or spend status changes """
    try:
        # Update the corresponding transaction when deposit or spend status changes
        transaction_type = 'DEPOSIT' if sender == Deposit else 'SPENT'
        transaction = Transactions.objects.filter(user=instance.user, type=transaction_type, amount=instance.amount).first()
        if transaction and instance.status != transaction.status:
            transaction.status = instance.status
            transaction.save()
    except Transactions.DoesNotExist:
        pass


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
