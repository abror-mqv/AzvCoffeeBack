from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    class DeliveryType(models.TextChoices):
        PICKUP = 'pickup', _('Забрать в кафе')
        DELIVERY = 'delivery', _('Доставка')

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Наличные')
        CARD = 'card', _('Карта на месте')
        ONLINE = 'online', _('Онлайн-оплата (заглушка)')

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Ожидает оплаты')
        PAID = 'paid', _('Оплачено')
        FAILED = 'failed', _('Ошибка оплаты')

    class Status(models.TextChoices):
        NEW = 'new', _('Новый')
        ACCEPTED = 'accepted', _('Принят')
        IN_PROGRESS = 'in_progress', _('Готовится')
        READY = 'ready', _('Готов к выдаче')
        COMPLETED = 'completed', _('Завершён')
        CANCELLED = 'cancelled', _('Отменён')

    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name=_('Клиент'))
    coffee_shop = models.ForeignKey('core.CoffeeShop', on_delete=models.PROTECT, related_name='orders', verbose_name=_('Заведение'))

    delivery_type = models.CharField(max_length=20, choices=DeliveryType.choices, default=DeliveryType.PICKUP, verbose_name=_('Тип получения'))
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH, verbose_name=_('Метод оплаты'))
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name=_('Статус оплаты'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, verbose_name=_('Статус заказа'))

    items_total_amount = models.IntegerField(default=0, verbose_name=_('Сумма позиций (в коп.)'))
    discount_amount = models.IntegerField(default=0, verbose_name=_('Скидка (в коп.)'))
    final_amount = models.IntegerField(default=0, verbose_name=_('Итого к оплате (в коп.)'))

    customer_comment = models.TextField(blank=True, null=True, verbose_name=_('Комментарий клиента'))

    delivery_address = models.CharField(max_length=512, blank=True, null=True, verbose_name=_('Адрес доставки'))
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('Широта доставки'))
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('Долгота доставки'))

    # Loyalty planning fields (applied when order is accepted by barista)
    planned_use_points = models.BooleanField(default=False, verbose_name=_('Планируется списание баллов'))
    planned_points_to_spend = models.IntegerField(default=0, verbose_name=_('План к списанию (в баллах)'))
    planned_earn_points = models.IntegerField(default=0, verbose_name=_('План к начислению (в баллах)'))
    planned_coffee_quantity = models.IntegerField(default=0, verbose_name=_('Плановое количество кофе'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Order #{self.id} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('Заказ'))
    item_variant = models.ForeignKey('menue.ItemVariant', on_delete=models.PROTECT, related_name='order_items', verbose_name=_('Вариант товара'))

    name_snapshot = models.CharField(max_length=200, verbose_name=_('Название на момент покупки'))
    portion_snapshot = models.CharField(max_length=100, verbose_name=_('Порция на момент покупки'))

    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Количество'))
    unit_price = models.IntegerField(verbose_name=_('Цена за единицу (в коп.)'))
    total_price = models.IntegerField(verbose_name=_('Сумма (в коп.)'))

    is_coffee = models.BooleanField(default=False, verbose_name=_('Кофе'))

    def __str__(self) -> str:
        return f"{self.name_snapshot} x{self.quantity}"

