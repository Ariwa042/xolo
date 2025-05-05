from django.contrib import admin
from .models import User, UserProfile, Deposit, Spend, Transactions, Payment_account


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('username', )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'xp_balance')
    search_fields = ('user__username', )
    ordering = ('user', )

@admin.register(Payment_account)
class Payment_accountAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_number', 'account_holder_name')
    list_filter = ('bank_name',)
    search_fields = ('bank_name', 'account_number', 'account_holder_name')
    ordering = ('bank_name',)
    
@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('deposit_id', 'user', 'amount', 'created_at', 'status')
    list_filter = ('status', )
    search_fields = ('user__username', 'deposit_id')
    ordering = ('-created_at', )


@admin.register(Spend)
class SpendAdmin(admin.ModelAdmin):
    list_display = ('spend_id', 'user', 'amount', 'created_at', 'status')
    list_filter = ('status', )
    search_fields = ('user__username', 'spend_id')
    ordering = ('-created_at', )


@admin.register(Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'amount', 'status', 'created_at')
    list_filter = ('type', 'status')
    search_fields = ('user__username', )
    ordering = ('-created_at', )
