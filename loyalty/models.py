from django.db import models
from django.utils import timezone
from core.models import User
import random
import string

# Create your models here.

class LoyaltyCode(models.Model):
    """Модель для хранения временных кодов лояльности пользователей"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loyalty_codes',
        verbose_name="Пользователь"
    )
    code = models.CharField(
        max_length=6,
        unique=True,
        verbose_name="Код лояльности"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время создания"
    )
    expires_at = models.DateTimeField(
        verbose_name="Время истечения"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    is_free_coffee_redemption = models.BooleanField(
        default=False,
        verbose_name="Код для получения бесплатного кофе"
    )
    
    class Meta:
        verbose_name = "Код лояльности"
        verbose_name_plural = "Коды лояльности"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Код {self.code} для {self.user.phone}"
    
    def is_expired(self):
        """Проверяет, истек ли срок действия кода"""
        return timezone.now() > self.expires_at
    
    def deactivate(self):
        """Деактивирует код"""
        self.is_active = False
        self.save()
    
    @classmethod
    def generate_code(cls):
        """Генерирует случайный 6-значный код"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_for_user(cls, user, expiration_minutes=15, is_free_coffee=False):
        """Создает новый код для пользователя и деактивирует старые"""
        # Деактивируем все старые коды пользователя
        cls.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Генерируем новый уникальный код
        while True:
            code = cls.generate_code()
            if not cls.objects.filter(code=code, is_active=True).exists():
                break
        
        # Создаем новый код с указанным сроком действия
        expires_at = timezone.now() + timezone.timedelta(minutes=expiration_minutes)
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=expires_at,
            is_free_coffee_redemption=is_free_coffee
        )


class LoyaltyTransaction(models.Model):
    """Модель для хранения транзакций начисления/списания бонусов"""
    
    TYPE_EARNING = 'earning'  # начисление
    TYPE_SPENDING = 'spending'  # списание
    
    TYPE_CHOICES = [
        (TYPE_EARNING, 'Начисление'),
        (TYPE_SPENDING, 'Списание'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions',
        verbose_name="Пользователь"
    )
    barista = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_transactions',
        verbose_name="Обработавший бариста",
        limit_choices_to={'role__in': ['barista', 'senior_barista']}
    )
    coffee_shop = models.ForeignKey(
        'core.CoffeeShop',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
        verbose_name="Кофейня"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Тип транзакции"
    )
    amount = models.IntegerField(
        verbose_name="Сумма чека (в копейках)"
    )
    points_used = models.IntegerField(
        default=0,
        verbose_name="Использовано бонусов"
    )
    points_earned = models.IntegerField(
        default=0,
        verbose_name="Начислено бонусов"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время создания"
    )
    
    class Meta:
        verbose_name = "Транзакция лояльности"
        verbose_name_plural = "Транзакции лояльности"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.points} баллов для {self.user.phone}"
