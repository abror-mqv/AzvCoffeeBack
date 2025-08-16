from rest_framework import generics, permissions, authentication, status
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification, NotificationReceipt
from .serializers import NotificationSerializer, NotificationSendSerializer
from core.models import User


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ROLE_MANAGER


class NotificationListView(generics.ListAPIView):
    """Список активных уведомлений для текущего пользователя (не истёкших)."""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        return Notification.objects.filter(
            receipts__user=user,
            expires_at__gt=now
        ).order_by('-created_at').distinct()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class NotificationSendView(generics.CreateAPIView):
    """Менеджер создаёт и рассылает уведомления (всем или выборочно)."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NotificationSendSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx
