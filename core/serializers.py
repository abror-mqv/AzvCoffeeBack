from rest_framework import serializers
from .models import User, CoffeeShop, Rank


class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для пользователей"""
    
    class Meta:
        model = User
        fields = ['id', 'phone', 'role', 'first_name', 'last_name', 'coffee_shop']
        read_only_fields = ['id', 'role']


class ClientPhoneCheckSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)


class ClientRegistrationSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=20)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    birth_date = serializers.DateField()

    class Meta:
        model = User
        fields = ['phone', 'first_name', 'last_name', 'birth_date', 'points', 'coffee_count', 'total_spent']

    def validate_phone(self, value):
        # Проверяем, что номер телефона не занят другими ролями
        if User.objects.filter(phone=value).exclude(role=User.ROLE_CLIENT).exists():
            raise serializers.ValidationError("Номер телефона уже используется в системе")
        return value

    def create(self, validated_data):
        # Создаем пользователя с ролью клиента
        user = User.objects.create(
            phone=validated_data['phone'],
            role=User.ROLE_CLIENT,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            birth_date=validated_data['birth_date']
        )
        return user


class BaristaLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(max_length=128)


class BaristaInfoSerializer(serializers.ModelSerializer):
    coffee_shop_name = serializers.SerializerMethodField()
    is_responsible = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'role', 'first_name', 'last_name',
            'coffee_shop', 'coffee_shop_name', 'is_responsible'
        ]
        
    def get_coffee_shop_name(self, obj):
        return obj.coffee_shop.name if obj.coffee_shop else None
        
    def get_is_responsible(self, obj):
        if obj.coffee_shop and obj.coffee_shop.responsible_senior_barista == obj:
            return True
        return False


class ClientInfoSerializer(serializers.ModelSerializer):
    free_coffee_count = serializers.SerializerMethodField()
    coffee_to_next_free = serializers.SerializerMethodField()
    total_spent_rubles = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    cashback_percent = serializers.SerializerMethodField()
    next_rank = serializers.SerializerMethodField()
    progress_to_next_percent = serializers.SerializerMethodField()
    rank_color = serializers.SerializerMethodField()
    rank_icon = serializers.SerializerMethodField()

    notifications = serializers.SerializerMethodField()
    redeem_token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'first_name', 'last_name', 'birth_date',
            'points', 'coffee_count', 'total_spent',
            'free_coffee_count', 'coffee_to_next_free', 'total_spent_rubles',
            'rank', 'cashback_percent', 'next_rank', 'progress_to_next_percent',
            'rank_color', 'rank_icon', 'notifications', 'redeem_token'
        ]

    def get_free_coffee_count(self, obj):
        return obj.get_free_coffee_count()

    def _rank_tuple(self, obj):
        from .models import Rank
        current, next_rank, progress = Rank.get_progress_percent(obj.total_spent)
        return current, next_rank, progress

    def get_rank(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return current.name if current else None

    def get_cashback_percent(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return current.cashback_percent if current else 0

    def get_next_rank(self, obj):
        _, next_rank, _ = self._rank_tuple(obj)
        return next_rank.name if next_rank else None

    def get_progress_to_next_percent(self, obj):
        _, _, progress = self._rank_tuple(obj)
        return progress

    def get_rank_color(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return getattr(current, 'color', None) if current else None

    def get_rank_icon(self, obj):
        current, _, _ = self._rank_tuple(obj)
        if current and getattr(current, 'icon', None):
            request = self.context.get('request') if hasattr(self, 'context') else None
            if request:
                try:
                    return request.build_absolute_uri(current.icon.url)
                except Exception:
                    return None
            return current.icon.url
        return None

    def get_notifications(self, obj):
        # Возвращаем активные (неистёкшие) уведомления для этого пользователя
        try:
            from notifications.models import Notification
            from notifications.serializers import NotificationSerializer
        except Exception:
            return []
        request = self.context.get('request') if hasattr(self, 'context') else None
        if not request or not request.user.is_authenticated:
            return []
        from django.utils import timezone
        qs = Notification.objects.filter(receipts__user=obj, expires_at__gt=timezone.now()).order_by('-created_at').distinct()
        return NotificationSerializer(qs, many=True, context={'request': request}).data

    def get_coffee_to_next_free(self, obj):
        return obj.get_coffee_to_next_free()

    def get_total_spent_rubles(self, obj):
        return obj.get_total_spent_rubles()

    def get_redeem_token(self, obj):
        try:
            from loyalty.models import LoyaltyCode
            from django.utils import timezone
            lc = LoyaltyCode.objects.filter(
                user=obj,
                is_active=True,
                is_free_coffee_redemption=True,
                expires_at__gt=timezone.now(),
            ).order_by('-created_at').first()
            return lc.code if lc else None
        except Exception:
            return None

    def _rank_tuple(self, obj):
        from .models import Rank
        current, next_rank, progress = Rank.get_progress_percent(obj.total_spent)
        return current, next_rank, progress

    def get_rank(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return current.name if current else None

    def get_cashback_percent(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return current.cashback_percent if current else 0

    def get_next_rank(self, obj):
        _, next_rank, _ = self._rank_tuple(obj)
        return next_rank.name if next_rank else None

    def get_progress_to_next_percent(self, obj):
        _, _, progress = self._rank_tuple(obj)
        return progress

    def get_rank_color(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return getattr(current, 'color', None) if current else None

    def get_rank_icon(self, obj):
        current, _, _ = self._rank_tuple(obj)
        if current and getattr(current, 'icon', None):
            request = self.context.get('request') if hasattr(self, 'context') else None
            if request:
                try:
                    return request.build_absolute_uri(current.icon.url)
                except Exception:
                    return None
            return current.icon.url
        return None


class ClientListSerializer(serializers.ModelSerializer):
    total_spent_rubles = serializers.SerializerMethodField()
    free_coffee_count = serializers.SerializerMethodField()
    registration_date = serializers.DateTimeField(source='date_joined', read_only=True, format='%Y-%m-%d')
    rank = serializers.SerializerMethodField()
    cashback_percent = serializers.SerializerMethodField()
    next_rank = serializers.SerializerMethodField()
    progress_to_next_percent = serializers.SerializerMethodField()
    rank_color = serializers.SerializerMethodField()
    rank_icon = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'first_name', 'last_name', 'birth_date',
            'points', 'coffee_count', 'total_spent', 'total_spent_rubles',
            'free_coffee_count', 'registration_date',
            'rank', 'cashback_percent', 'next_rank', 'progress_to_next_percent',
            'rank_color', 'rank_icon'
        ]

    def _rank_tuple(self, obj):
        from .models import Rank
        current, next_rank, progress = Rank.get_progress_percent(obj.total_spent)
        return current, next_rank, progress

    def get_rank(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return current.name if current else None

    def get_cashback_percent(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return current.cashback_percent if current else 0

    def get_next_rank(self, obj):
        _, next_rank, _ = self._rank_tuple(obj)
        return next_rank.name if next_rank else None

    def get_progress_to_next_percent(self, obj):
        _, _, progress = self._rank_tuple(obj)
        return progress

    def get_total_spent_rubles(self, obj):
        return obj.get_total_spent_rubles()

    def get_free_coffee_count(self, obj):
        return obj.get_free_coffee_count()

    def get_rank_color(self, obj):
        current, _, _ = self._rank_tuple(obj)
        return getattr(current, 'color', None) if current else None

    def get_rank_icon(self, obj):
        current, _, _ = self._rank_tuple(obj)
        if current and getattr(current, 'icon', None):
            request = self.context.get('request') if hasattr(self, 'context') else None
            if request:
                try:
                    return request.build_absolute_uri(current.icon.url)
                except Exception:
                    return None
            return current.icon.url
        return None


class CoffeeShopSerializer(serializers.ModelSerializer):
    opening_hours = serializers.JSONField(required=False)
    responsible_senior_barista_phone = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()

    class Meta:
        model = CoffeeShop
        fields = [
            'id', 'name', 'address', 'latitude', 'longitude', 
            'opening_hours', 'responsible_senior_barista_phone', 'staff_count'
        ]

    def get_responsible_senior_barista_phone(self, obj):
        if obj.responsible_senior_barista:
            return obj.responsible_senior_barista.phone
        return None

    def get_staff_count(self, obj):
        return obj.staff.filter(role__in=[User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA]).count()


class WorkingHoursSerializer(serializers.Serializer):
    day_of_week = serializers.IntegerField(min_value=0, max_value=6)
    opening_time = serializers.CharField(max_length=5)
    closing_time = serializers.CharField(max_length=5)

    def validate_opening_time(self, value):
        # Проверка формата времени (HH:MM)
        if not self._is_valid_time_format(value):
            raise serializers.ValidationError("Время должно быть в формате HH:MM")
        return value

    def validate_closing_time(self, value):
        # Проверка формата времени (HH:MM)
        if not self._is_valid_time_format(value):
            raise serializers.ValidationError("Время должно быть в формате HH:MM")
        return value

    def _is_valid_time_format(self, time_str):
        try:
            hours, minutes = time_str.split(':')
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                return False
            return True
        except (ValueError, IndexError):
            return False 


class RankSerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Rank
        fields = ['id', 'name', 'min_total_spent_som', 'cashback_percent', 'color', 'icon_url']

    def get_icon_url(self, obj):
        if getattr(obj, 'icon', None):
            request = self.context.get('request') if hasattr(self, 'context') else None
            try:
                url = obj.icon.url
            except Exception:
                return None
            if request:
                return request.build_absolute_uri(url)
            return url
        return None