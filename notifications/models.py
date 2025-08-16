from django.db import models
from django.utils import timezone
import uuid


class Notification(models.Model):
    """Внутренние уведомления для пользователей.

    Поля:
    - uid: публичный идентификатор
    - text: текст уведомления
    - type: тип уведомления (generic | transaction)
    - expires_at: срок жизни
    - created_at: время создания
    - created_by: кто создал (обычно менеджер или система)
    - recipients: адресаты (список пользователей)
    - is_read: признак прочтения (пер-пользователю храним в through модели)
    """

    TYPE_GENERIC = 'generic'
    TYPE_TRANSACTION = 'transaction'
    TYPE_CHOICES = (
        (TYPE_GENERIC, 'Generic'),
        (TYPE_TRANSACTION, 'Transaction'),
    )

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    text = models.TextField()
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_GENERIC)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_notifications'
    )

    recipients = models.ManyToManyField(
        'core.User', through='NotificationReceipt', related_name='notifications'
    )

    class Meta:
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['type']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type}: {self.text[:40]}"

    @classmethod
    def create_for_recipients(cls, text: str, ntype: str, recipients, expires_at, created_by=None):
        n = cls.objects.create(text=text, type=ntype, expires_at=expires_at, created_by=created_by)
        # bulk link recipients
        receipts = [NotificationReceipt(notification=n, user=u) for u in recipients]
        NotificationReceipt.objects.bulk_create(receipts)
        return n


class NotificationReceipt(models.Model):
    """Связка уведомления и пользователя с признаком прочтения."""

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='receipts')
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='notification_receipts')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('notification', 'user')
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

# Create your models here.
