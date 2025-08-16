from django.contrib import admin
from .models import Notification, NotificationReceipt


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('uid', 'type', 'text', 'expires_at', 'created_at', 'created_by')
    list_filter = ('type', )
    search_fields = ('text', 'uid')


@admin.register(NotificationReceipt)
class NotificationReceiptAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'is_read', 'read_at')
    list_filter = ('is_read', )
    search_fields = ('notification__text', 'user__phone')
