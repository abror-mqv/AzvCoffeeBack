from django.contrib import admin
from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'coffee_shop', 'status', 'payment_status',
        'items_total_amount', 'final_amount', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'coffee_shop')
    search_fields = ('id', 'user__phone', 'coffee_shop__name')
    date_hierarchy = 'created_at'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'order', 'name_snapshot', 'portion_snapshot',
        'quantity', 'unit_price', 'total_price', 'is_coffee'
    )
    search_fields = ('name_snapshot', 'order__id')
