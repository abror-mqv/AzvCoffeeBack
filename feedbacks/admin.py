from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'coffee_shop', 'user', 'created_at')
    list_filter = ('type', 'coffee_shop', 'created_at')
    search_fields = ('user__phone', 'user__first_name', 'user__last_name', 'text')
