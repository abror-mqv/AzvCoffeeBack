from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from core.models import User, CoffeeShop
from .models import LoyaltyCode, LoyaltyTransaction
from django.utils import timezone

# Create your tests here.

class LoyaltyTransactionTest(TestCase):
    def setUp(self):
        # Создаем кофейню
        self.coffee_shop = CoffeeShop.objects.create(
            name="Test Coffee Shop",
            address="Test Address"
        )
        
        # Создаем клиента
        self.client_user = User.objects.create(
            phone="+70001112233",
            role=User.ROLE_CLIENT,
            first_name="Test",
            last_name="Client"
        )
        self.client_token = Token.objects.create(user=self.client_user)
        
        # Создаем баристу
        self.barista_user = User.objects.create(
            phone="+70004445566",
            role=User.ROLE_BARISTA,
            first_name="Test",
            last_name="Barista",
            coffee_shop=self.coffee_shop
        )
        self.barista_user.password = "testpassword"
        self.barista_user.save()
        self.barista_token = Token.objects.create(user=self.barista_user)
        
        # Создаем код лояльности для клиента
        self.loyalty_code = LoyaltyCode.create_for_user(self.client_user)
        
        # Настраиваем API клиент
        self.api_client = APIClient()
    
    def test_transaction_amount_in_currency(self):
        """
        Тест для проверки, что сумма транзакции правильно преобразуется из сомов в копейки
        """
        # Авторизуемся как бариста
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.barista_token.key}')
        
        # Создаем транзакцию с суммой в сомах (100 сом)
        url = reverse('loyalty:create_transaction')
        data = {
            'code': self.loyalty_code.code,
            'amount': 100,  # 100 сом
            'transaction_type': LoyaltyTransaction.TYPE_EARNING
        }
        
        response = self.api_client.post(url, data)
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что транзакция сохранена с суммой в копейках (10000 копеек)
        transaction = LoyaltyTransaction.objects.latest('created_at')
        self.assertEqual(transaction.amount, 10000)  # 100 * 100 = 10000 копеек
        
        # Проверяем, что в ответе есть поле amount_in_currency с правильной суммой в сомах
        self.assertEqual(response.data['transaction']['amount'], 10000)
        self.assertEqual(response.data['transaction']['amount_in_currency'], 100)
