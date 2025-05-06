from django.contrib import admin
from .models import (
    User, UserProfile, Transactions, Payment_account,
    SubscriptionPlan, Subscription, Deposit
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('username', )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_active_subscription', 'subscription_override', 'max_monthly_emails')
    search_fields = ('user__username', 'notes')
    list_filter = ('subscription_override',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Subscription Override', {
            'fields': ('subscription_override', 'subscription_end_date', 'max_emails_override', 'notes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Payment_account)
class Payment_accountAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_number', 'account_holder_name')
    list_filter = ('bank_name',)
    search_fields = ('bank_name', 'account_number', 'account_holder_name')
    ordering = ('bank_name',)
    
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'price', 'max_emails_per_month', 'duration_days')
    search_fields = ('template__type',)
    list_filter = ('duration_days',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__username',)
    list_filter = ('is_active',)
    readonly_fields = ('start_date',)

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('deposit_id', 'user', 'subscription_plan', 'get_amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'deposit_id')
    readonly_fields = ('deposit_id', 'get_amount', 'created_at')
    ordering = ('-created_at',)

    def has_receipt(self, obj):
        return bool(obj.receipt)
    has_receipt.boolean = True
    has_receipt.short_description = 'Has Receipt'

    def get_amount(self, obj):
        return obj.amount if obj.subscription_plan else 0
    get_amount.short_description = 'Amount'

@admin.register(Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription', 'amount', 'status', 'created_at')
    list_filter = ('status', 'subscription__is_active')
    search_fields = ('user__username',)
    readonly_fields = ('amount', 'created_at')
    ordering = ('-created_at',)
