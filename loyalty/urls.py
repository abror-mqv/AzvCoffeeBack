from django.urls import path
from .views import (
    LoyaltyCodeView,
    LoyaltyFreeCoffeeCodeView,
    LoyaltyCodeVerifyView,
    LoyaltyCodeStatusView,
    LoyaltyTransactionCreateView,
    LoyaltyTransactionHistoryView,
    LoyaltyFreeCoffeeConfirmView
)

app_name = 'loyalty'

urlpatterns = [
    # Маршрут для генерации кода лояльности (для клиента)
    path('loyalty/code/generate/', LoyaltyCodeView.as_view(), name='generate_code'),
    
    # Маршрут для генерации кода бесплатного кофе (для клиента)
    path('loyalty/code/generate-free/', LoyaltyFreeCoffeeCodeView.as_view(), name='generate_free_coffee_code'),
    
    # Маршрут для проверки кода лояльности (для баристы)
    path('loyalty/code/verify/', LoyaltyCodeVerifyView.as_view(), name='verify_code'),
    # Клиентский polling статуса кода
    path('loyalty/code/status/', LoyaltyCodeStatusView.as_view(), name='code_status'),
    
    # Маршрут для создания транзакции (начисление/списание баллов) (для баристы)
    path('loyalty/transaction/create/', LoyaltyTransactionCreateView.as_view(), name='create_transaction'),
    
    # Маршрут для получения истории транзакций
    path('loyalty/transactions/', LoyaltyTransactionHistoryView.as_view(), name='transaction_history'),

    # Подтверждение выдачи бесплатного кофе (бариста)
    path('loyalty/free-coffee/confirm/', LoyaltyFreeCoffeeConfirmView.as_view(), name='free_coffee_confirm'),
] 