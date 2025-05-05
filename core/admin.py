# Register your models here.
from django.contrib import admin
from .models import Campaign, VictimInfo, Wallet, Cryptocurrency, EmailTemplate

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipient_email', 'email_template', 'cryptocurrency', 'quantity', 'min_balance', 'created_at')
    search_fields = ('id', 'recipient_email', 'user__username', 'cryptocurrency')
    ordering = ('-created_at',)
    list_filter = ('email_template', 'cryptocurrency', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(VictimInfo)
class VictimInfoAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'wallet', 'campaign', 'address', 'created_at')
    search_fields = ('id','recipient_email', 'user__username', 'wallet', 'created_at')
    ordering = ('-created_at',)
    list_filter = ('wallet', 'created_at')
    readonly_fields = ('created_at',)

class CrytocurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'created_at')
    search_fields = ('name', 'symbol')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)

class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('type', 'xp_cost',)
    search_fields = ('type',)
    list_filter = ('type',)

admin.site.register(Cryptocurrency)
admin.site.register(Wallet)
admin.site.register(EmailTemplate)