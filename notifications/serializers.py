from rest_framework import serializers
from django.utils import timezone
from .models import Notification, NotificationReceipt
from core.models import User


class NotificationSerializer(serializers.ModelSerializer):
    uid = serializers.UUIDField(read_only=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True)

    class Meta:
        model = Notification
        fields = ['uid', 'text', 'type', 'expires_at', 'created_at', 'created_by_id']


class NotificationSendSerializer(serializers.Serializer):
    text = serializers.CharField()
    type = serializers.ChoiceField(choices=[(Notification.TYPE_GENERIC, 'generic'), (Notification.TYPE_TRANSACTION, 'transaction')], default=Notification.TYPE_GENERIC)
    recipients_all = serializers.BooleanField(required=False, default=False)
    recipient_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    ttl_hours = serializers.IntegerField(required=False, min_value=1)
    expires_at = serializers.DateTimeField(required=False)

    def validate(self, data):
        ttl = data.get('ttl_hours')
        exp = data.get('expires_at')
        if not ttl and not exp:
            raise serializers.ValidationError({'ttl_hours': 'Укажите ttl_hours или expires_at'})
        if ttl and exp:
            raise serializers.ValidationError({'ttl_hours': 'Укажите только одно: ttl_hours или expires_at'})
        if data.get('recipients_all'):
            return data
        if not data.get('recipient_ids'):
            raise serializers.ValidationError({'recipient_ids': 'Укажите получателей или recipients_all=true'})
        return data

    def create(self, validated_data):
        request = self.context['request']
        ttl = validated_data.get('ttl_hours')
        expires_at = validated_data.get('expires_at') or (timezone.now() + timezone.timedelta(hours=ttl))
        text = validated_data['text']
        ntype = validated_data.get('type', Notification.TYPE_GENERIC)

        if validated_data.get('recipients_all'):
            recipients = list(User.objects.filter(role=User.ROLE_CLIENT))
        else:
            ids = validated_data.get('recipient_ids', [])
            recipients = list(User.objects.filter(id__in=ids))
        n = Notification.create_for_recipients(text=text, ntype=ntype, recipients=recipients, expires_at=expires_at, created_by=request.user)
        return n
