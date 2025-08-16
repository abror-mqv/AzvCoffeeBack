from django.db import models
from core.models import User, CoffeeShop

class Feedback(models.Model):
    """Отзыв клиента о заведении"""
    TYPE_IDEA = 'idea'
    TYPE_SERVICE = 'service'
    TYPE_CHOICES = [
        (TYPE_IDEA, 'Предложение идеи'),
        (TYPE_SERVICE, 'Отзыв об обслуживании'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks', verbose_name='Клиент')
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='feedbacks', verbose_name='Заведение')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SERVICE, verbose_name='Тип отзыва')
    text = models.TextField(verbose_name='Текст отзыва')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f"Feedback #{self.id} ({self.type}) by {self.user.phone} for {self.coffee_shop.name}"

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
