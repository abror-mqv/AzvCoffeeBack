from django.shortcuts import render
from rest_framework import viewsets, status, generics, authentication
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import LoyaltyCode, LoyaltyTransaction
from .serializers import (
    LoyaltyCodeSerializer,
    LoyaltyTransactionSerializer,
    LoyaltyCodeVerificationSerializer,
    LoyaltyTransactionCreateSerializer
)
from core.models import User
from django.utils import timezone



class LoyaltyCodeView(generics.CreateAPIView):
    """Представление для генерации кода лояльности для клиента"""
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = LoyaltyCodeSerializer
    
    def create(self, request, *args, **kwargs):
        print("checkpint")
        user = request.user
        
        # Только клиенты могут генерировать коды лояльности
        if user.role != User.ROLE_CLIENT:
            return Response(
                {"error": "Только клиенты могут генерировать коды лояльности"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Создаем новый код для пользователя
        loyalty_code = LoyaltyCode.create_for_user(user)
        serializer = self.get_serializer(loyalty_code)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoyaltyFreeCoffeeCodeView(generics.CreateAPIView):
    """Представление для генерации кода для получения бесплатного кофе"""
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = LoyaltyCodeSerializer
    
    def create(self, request, *args, **kwargs):
        user = request.user
        
        # Только клиенты могут генерировать коды лояльности
        if user.role != User.ROLE_CLIENT:
            return Response(
                {"error": "Только клиенты могут генерировать коды лояльности"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Проверяем, что у клиента достаточно кофе для бесплатного
        if user.coffee_count < 7:
            return Response(
                {
                    "error": "Недостаточно кофе для получения бесплатного",
                    "coffee_count": user.coffee_count,
                    "coffee_needed": 7
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем новый код для бесплатного кофе
        loyalty_code = LoyaltyCode.create_for_user(user, is_free_coffee=True)
        serializer = self.get_serializer(loyalty_code)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoyaltyCodeVerifyView(generics.GenericAPIView):
    """Представление для проверки кода лояльности"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = LoyaltyCodeVerificationSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Проверка роли (только бариста может проверять коды)
        user = request.user
        if user.role not in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA]:
            return Response(
                {"error": "Только бариста может проверять коды лояльности"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        code = serializer.validated_data['code']
        
        try:
            # Ищем активный и не истекший код
            loyalty_code = LoyaltyCode.objects.get(code=code, is_active=True)
            
            # Проверяем срок действия
            if loyalty_code.is_expired():
                return Response(
                    {"error": "Срок действия кода истек"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Валидация прошла, но больше НЕ деактивируем код на этапе верификации.
            # Код деактивируется только при успешном создании транзакции.
            try:
                print(f"[LoyaltyCodeVerifyView] Verified code without deactivation: code={loyalty_code.code}")
            except Exception:
                pass

            # Возвращаем информацию о пользователе, которому принадлежит код
            user_data = {
                "id": loyalty_code.user.id,
                "phone": loyalty_code.user.phone,
                "first_name": loyalty_code.user.first_name,
                "last_name": loyalty_code.user.last_name,
                "points": loyalty_code.user.points,
                "coffee_count": loyalty_code.user.coffee_count,
                "coffee_to_next_free": loyalty_code.user.get_coffee_to_next_free()
            }
            
            return Response(
                {
                    "success": True,
                    "user": user_data
                },
                status=status.HTTP_200_OK
            )
            
        except LoyaltyCode.DoesNotExist:
            return Response(
                {"error": "Неверный код"},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoyaltyCodeStatusView(generics.GenericAPIView):
    """Клиентский чек статуса QR-кода: active | used | expired.

    Клиент опрашивает раз в секунду. Когда статус становится used,
    фронт делает редирект на главную.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, *args, **kwargs):
        code = request.query_params.get("code")
        if not code:
            return Response({"error": "Параметр code обязателен"}, status=status.HTTP_400_BAD_REQUEST)
        if not code.isdigit() or len(code) != 6:
            return Response({"error": "Неверный формат code"}, status=status.HTTP_400_BAD_REQUEST)

        # Только коды текущего пользователя
        try:
            lc = LoyaltyCode.objects.get(code=code, user=request.user)
        except LoyaltyCode.DoesNotExist:
            return Response({"error": "Код не найден"}, status=status.HTTP_404_NOT_FOUND)

        is_expired = lc.is_expired()
        is_active = lc.is_active and not is_expired
        used = (not lc.is_active) and not is_expired

        status_str = "active" if is_active else ("used" if used else "expired")

        return Response({
            "code": lc.code,
            "status": status_str,
            "is_active": is_active,
            "is_expired": is_expired,
            "used": used,
            "should_redirect": used
        }, status=status.HTTP_200_OK)


class LoyaltyTransactionCreateView(generics.CreateAPIView):
    """
    Создание транзакции лояльности
    
    Бариста сканирует код клиента, вводит сумму чека и количество списываемых бонусов.
    Система начисляет 5% бонусов от суммы после вычета использованных бонусов.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = LoyaltyTransactionCreateSerializer
    
    def create(self, request, *args, **kwargs):
        try:
            print(f"[LoyaltyTransactionCreateView.create] Raw body: {request.body}")
        except Exception:
            pass
        try:
            print(
                f"[LoyaltyTransactionCreateView.create] User id={getattr(request.user, 'id', None)}, "
                f"role={getattr(request.user, 'role', None)}, "
                f"coffee_shop_id={getattr(getattr(request.user, 'coffee_shop', None), 'id', None)}"
            )
        except Exception:
            pass
        # Проверка роли (только бариста может создавать транзакции)
        if request.user.role not in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA]:
            return Response(
                {"error": "Только бариста может создавать транзакции"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Проверяем, что бариста привязан к кофейне
        if not request.user.coffee_shop:
            return Response(
                {"error": "Бариста должен быть привязан к кофейне"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            try:
                print(f"[LoyaltyTransactionCreateView.create] ValidationError: {ve.detail}")
            except Exception:
                pass
            raise
        
        try:
            transaction = serializer.save()
            result_serializer = LoyaltyTransactionSerializer(transaction)
            
            # Получаем обновленную информацию о пользователе
            customer = transaction.user
            user_data = {
                "id": customer.id,
                "phone": customer.phone,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "points": customer.points,
                "coffee_count": customer.coffee_count,
                "coffee_to_next_free": customer.get_coffee_to_next_free()
            }
            
            # Создаём уведомление для клиента (TTL 48 часов)
            try:
                from notifications.models import Notification
                expires_at = timezone.now() + timezone.timedelta(days=2)
                text = (
                    f"Покупка проведена. Сумма: {transaction.amount/100:.2f} сом. "
                    f"Начислено: {transaction.points_earned} баллов. "
                    f"Списано: {transaction.points_used} баллов."
                )
                Notification.create_for_recipients(
                    text=text,
                    ntype=Notification.TYPE_TRANSACTION,
                    recipients=[customer],
                    expires_at=expires_at,
                    created_by=request.user,
                )
            except Exception:
                # Не блокируем основной флоу, если уведомление не создалось
                pass

            return Response(
                {
                    "transaction": result_serializer.data,
                    "user": user_data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            try:
                print(f"[LoyaltyTransactionCreateView.create] Exception during save/respond: {e}")
            except Exception:
                pass
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoyaltyTransactionHistoryView(generics.ListAPIView):
    """Представление для просмотра истории транзакций лояльности"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = LoyaltyTransactionSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Для клиента - только его транзакции
        if user.role == User.ROLE_CLIENT:
            return LoyaltyTransaction.objects.filter(user=user)
        
        # Для бариста - только транзакции его кофейни
        elif user.role in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA] and user.coffee_shop:
            return LoyaltyTransaction.objects.filter(coffee_shop=user.coffee_shop)
        
        # Для менеджера - все транзакции
        elif user.role == User.ROLE_MANAGER:
            return LoyaltyTransaction.objects.all()
        
        # Для остальных - пустой список
        return LoyaltyTransaction.objects.none()
