from django.contrib import admin
from .models import Category, MenuItem, Portion, ItemVariant

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)

@admin.register(Portion)
class PortionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "volume", "unit")
    search_fields = ("name",)

class ItemVariantInline(admin.TabularInline):
    model = ItemVariant
    extra = 1

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "get_default_price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "ingredients")
    inlines = [ItemVariantInline]
    
    def get_default_price(self, obj):
        default_variant = obj.variants.filter(is_default=True).first()
        if default_variant:
            return default_variant.price
        return "-"
    get_default_price.short_description = "Цена"

@admin.register(ItemVariant)
class ItemVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "menu_item", "portion", "price", "is_default")
    list_filter = ("menu_item__category", "is_default")
    search_fields = ("menu_item__name",)
