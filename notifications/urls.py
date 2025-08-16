from django.urls import path
from .views import NotificationListView, NotificationSendView

app_name = 'notifications'

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='list'),
    path('notifications/send/', NotificationSendView.as_view(), name='send'),
]
