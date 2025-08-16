from django.contrib import admin
from .models import LoyaltyCode, LoyaltyTransaction

@admin.register(LoyaltyCode)
class LoyaltyCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'created_at', 'expires_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'user__phone', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)
    
@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'barista', 'coffee_shop', 'transaction_type', 'amount', 'points_used', 'points_earned', 'created_at')
    list_filter = ('transaction_type', 'coffee_shop')
    search_fields = ('user__phone', 'barista__phone', 'coffee_shop__name')
    readonly_fields = ('created_at',)
