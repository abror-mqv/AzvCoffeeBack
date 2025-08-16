from django.contrib import admin
from .models import User, CoffeeShop, Rank

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone", "role", "coffee_shop", "is_active", "is_staff")
    list_filter = ("role", "coffee_shop", "is_active")
    search_fields = ("phone",)

@admin.register(CoffeeShop)
class CoffeeShopAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "created_at")
    search_fields = ("name", "address")


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ("name", "min_total_spent_som", "cashback_percent", "color", "icon")
    list_editable = ("min_total_spent_som", "cashback_percent", "color")
    ordering = ("min_total_spent_som",)
