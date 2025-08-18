from rest_framework import serializers
from django.db import transaction
from .models import LoyaltyCode, LoyaltyTransaction
from core.models import User, Rank
from core.serializers import UserSerializer

class LoyaltyCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для кодов лояльности"""
    
    class Meta:
        model = LoyaltyCode
        fields = ['id', 'code', 'created_at', 'expires_at', 'is_active']
        read_only_fields = ['id', 'code', 'created_at', 'expires_at']


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    """Сериализатор для транзакций лояльности"""
    
    user_info = UserSerializer(source='user', read_only=True)
    barista_info = UserSerializer(source='barista', read_only=True)
    amount_in_currency = serializers.SerializerMethodField()
    final_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyaltyTransaction
        fields = [
            'id', 'user', 'user_info', 'barista', 'barista_info', 'coffee_shop',
            'transaction_type', 'amount', 'amount_in_currency', 'points_used',
            'points_earned', 'final_amount', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        
    def get_amount_in_currency(self, obj):
        """Возвращает сумму в целых денежных единицах (сомах)"""
        return obj.amount / 100
        
    def get_final_amount(self, obj):
        """Возвращает итоговую сумму к оплате после списания бонусов"""
        return (obj.amount - obj.points_used) / 100 if obj.transaction_type == LoyaltyTransaction.TYPE_EARNING else obj.amount / 100


class LoyaltyCodeVerificationSerializer(serializers.Serializer):
    """Сериализатор для верификации кода лояльности (6 или 8 цифр)"""
    code = serializers.CharField(max_length=8, required=True)

    def validate_code(self, value):
        if not value.isdigit() or len(value) not in (6, 8):
            raise serializers.ValidationError("Код должен состоять из 6 или 8 цифр")
        return value
    

class LoyaltyTransactionCreateSerializer(serializers.Serializer):
    """Сериализатор для создания транзакции лояльности"""
    
    code = serializers.CharField(max_length=6, required=True)
    amount = serializers.IntegerField(min_value=0, required=True)  # сумма в сомах
    points_to_use = serializers.IntegerField(min_value=0, required=True)
    coffee_quantity = serializers.IntegerField(min_value=0, default=0)
    
    def validate(self, data):
        code = data.get('code')
        points_to_use = data.get('points_to_use', 0)
        amount = data.get('amount', 0)
        coffee_quantity = data.get('coffee_quantity', 0)
        try:
            print(f"[LoyaltyTransactionCreateSerializer.validate] Incoming: code={code}, amount={amount}, points_to_use={points_to_use}, coffee_quantity={coffee_quantity}")
        except Exception:
            pass
        
        try:
            code_obj = LoyaltyCode.objects.get(code=code, is_active=True)
            if code_obj.is_expired():
                try:
                    print(f"[LoyaltyTransactionCreateSerializer.validate] Code expired: code={code}")
                except Exception:
                    pass
                raise serializers.ValidationError({"code": "Код истек"})
            
            user = code_obj.user

            # Нельзя проводить платную транзакцию по коду бесплатного кофе
            if code_obj.is_free_coffee_redemption:
                raise serializers.ValidationError({"code": "Это код для бесплатного кофе. Используйте подтверждение выдачи бесплатного кофе."})
            
            if points_to_use > user.points:
                try:
                    print(f"[LoyaltyTransactionCreateSerializer.validate] Not enough points: requested={points_to_use}, available={user.points}")
                except Exception:
                    pass
                raise serializers.ValidationError({
                    "points_to_use": f"Недостаточно бонусов. Доступно: {user.points}"
                })
                
            if points_to_use > amount:
                try:
                    print(f"[LoyaltyTransactionCreateSerializer.validate] Points exceed amount: points_to_use={points_to_use}, amount={amount}")
                except Exception:
                    pass
                raise serializers.ValidationError({
                    "points_to_use": "Нельзя использовать больше бонусов, чем сумма чека"
                })
                
            data['code_obj'] = code_obj
            try:
                print(f"[LoyaltyTransactionCreateSerializer.validate] Validation OK for code={code}")
            except Exception:
                pass
            return data
            
        except LoyaltyCode.DoesNotExist:
            try:
                print(f"[LoyaltyTransactionCreateSerializer.validate] Code not found or inactive: code={code}")
            except Exception:
                pass
            raise serializers.ValidationError({"code": "Неверный код"})
    
    def create(self, validated_data):
        code_obj = validated_data.pop('code_obj')
        user = code_obj.user
        amount = validated_data['amount']
        points_to_use = validated_data['points_to_use']
        coffee_quantity = validated_data.get('coffee_quantity', 0)
        barista = self.context['request'].user
        coffee_shop = barista.coffee_shop
        
        if not coffee_shop:
            try:
                print(f"[LoyaltyTransactionCreateSerializer.create] Barista has no coffee_shop. barista_id={getattr(barista, 'id', None)}")
            except Exception:
                pass
            raise serializers.ValidationError({"error": "Бариста не привязан к кофейне"})
        
        # Рассчитываем сумму для начисления бонусов (после вычета использованных бонусов)
        amount_for_points = max(0, amount - points_to_use)
        # Определяем кэшбек по рангу пользователя
        current_rank = Rank.get_current_for_total_spent(user.total_spent)
        cashback_percent = current_rank.cashback_percent if current_rank else 0
        points_earned = int(amount_for_points * (cashback_percent / 100.0))
        
        # Создаем транзакцию
        try:
            print(
                f"[LoyaltyTransactionCreateSerializer.create] Creating transaction: user_id={user.id}, barista_id={barista.id}, shop_id={coffee_shop.id}, "
                f"amount_som={amount}, points_to_use={points_to_use}, points_earned={points_earned}, coffee_qty={coffee_quantity}, cashback_percent={cashback_percent}"
            )
        except Exception:
            pass
        trx = LoyaltyTransaction.objects.create(
            user=user,
            barista=barista,
            coffee_shop=coffee_shop,
            transaction_type=LoyaltyTransaction.TYPE_EARNING,
            amount=amount * 100,  # конвертируем в копейки
            points_used=points_to_use,
            points_earned=points_earned
        )
        
        # Обновляем данные пользователя и выпускаем бесплатный токен при достижении 7
        with transaction.atomic():
            user.points = user.points - points_to_use + points_earned
            before = user.coffee_count or 0
            after = before + (coffee_quantity or 0)

            # Проверяем наличие активного бесплатного токена
            has_active_free = LoyaltyCode.objects.filter(user=user, is_active=True, is_free_coffee_redemption=True).exists()

            if has_active_free:
                # Штампы не накапливаются выше 6, пока есть активный бесплатный токен
                user.coffee_count = min(6, after)
            else:
                if after >= 7:
                    # Выдали один бесплатный токен, стакать нельзя
                    user.coffee_count = max(0, after - 7)
                    # Кэп на 6 в случае очень большого заказа
                    user.coffee_count = min(user.coffee_count, 6)
                    try:
                        LoyaltyCode.create_free_for_user(user)
                    except Exception:
                        # Даже если выпуск кода не удался, не падаем транзакцией продаж
                        pass
                else:
                    user.coffee_count = after

            user.total_spent += amount * 100  # в копейках
            user.save()
        
        # Деактивируем код
        try:
            print(f"[LoyaltyTransactionCreateSerializer.create] Deactivating code: code={code_obj.code}")
        except Exception:
            pass
        code_obj.deactivate()
        
        return trx