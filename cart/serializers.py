from decimal import Decimal
from typing import List
from rest_framework import serializers
from .models import Order, OrderItem
from menue.models import ItemVariant


class OrderItemInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    is_coffee = serializers.BooleanField(default=False)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'item_variant', 'name_snapshot', 'portion_snapshot',
            'quantity', 'unit_price', 'total_price', 'is_coffee'
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    coffee_shop_id = serializers.IntegerField()
    delivery_type = serializers.ChoiceField(choices=Order.DeliveryType.choices)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    customer_comment = serializers.CharField(allow_blank=True, required=False)
    delivery_address = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    use_points = serializers.BooleanField(required=False, default=False)
    items = OrderItemInputSerializer(many=True)

    def validate(self, data):
        # delivery constraints
        dt = data.get('delivery_type')
        addr = data.get('delivery_address')
        if dt == Order.DeliveryType.DELIVERY:
            if not addr or not str(addr).strip():
                raise serializers.ValidationError({'delivery_address': 'Адрес обязателен для доставки'})
        else:
            # For pickup, clear any address provided to avoid confusion
            data['delivery_address'] = None
        # items exist
        if not data['items']:
            raise serializers.ValidationError({'items': 'Список позиций не может быть пустым'})
        return data

    def create(self, validated_data):
        request = self.context['request']
        user = request.user if request.user.is_authenticated else None

        from core.models import CoffeeShop
        try:
            coffee_shop = CoffeeShop.objects.get(id=validated_data['coffee_shop_id'])
        except CoffeeShop.DoesNotExist:
            raise serializers.ValidationError({'coffee_shop_id': 'Заведение не найдено'})

        order = Order.objects.create(
            user=user,
            coffee_shop=coffee_shop,
            delivery_type=validated_data['delivery_type'],
            payment_method=validated_data['payment_method'],
            payment_status=Order.PaymentStatus.PENDING,
            status=Order.Status.NEW,
            customer_comment=validated_data.get('customer_comment') or '',
            delivery_address=validated_data.get('delivery_address'),
        )

        items_total = 0
        created_items: List[OrderItem] = []

        planned_coffee_qty = 0
        for item in validated_data['items']:
            variant_id = item['variant_id']
            quantity = item['quantity']
            is_coffee = item.get('is_coffee', False)

            try:
                variant = ItemVariant.objects.select_related('menu_item', 'portion').get(id=variant_id)
            except ItemVariant.DoesNotExist:
                raise serializers.ValidationError({'items': f'Вариант товара id={variant_id} не найден'})

            # price: Decimal (som) -> int (kopecks)
            unit_price_kop = int(Decimal(variant.price) * 100)
            total_price_kop = unit_price_kop * quantity

            oi = OrderItem(
                order=order,
                item_variant=variant,
                name_snapshot=variant.menu_item.name,
                portion_snapshot=str(variant.portion),
                quantity=quantity,
                unit_price=unit_price_kop,
                total_price=total_price_kop,
                is_coffee=is_coffee,
            )
            created_items.append(oi)
            items_total += total_price_kop
            if is_coffee:
                planned_coffee_qty += quantity

        OrderItem.objects.bulk_create(created_items)

        # Loyalty planning
        planned_use_points = bool(validated_data.get('use_points', False)) if user else False
        planned_points_to_spend = 0
        if user and planned_use_points:
            max_spend_som = items_total // 100
            planned_points_to_spend = min(user.points, max_spend_som)
        # Earn percent by current rank
        planned_earn_points = 0
        if user:
            try:
                from core.models import Rank
                current, _, _ = Rank.get_progress_percent(user.total_spent)
                percent = current.cashback_percent if current else 0
            except Exception:
                percent = 0
            planned_earn_points = (items_total // 100) * percent // 100

        order.items_total_amount = items_total
        order.discount_amount = planned_points_to_spend * 100
        order.final_amount = items_total - order.discount_amount
        order.planned_use_points = planned_use_points
        order.planned_points_to_spend = planned_points_to_spend
        order.planned_earn_points = planned_earn_points
        order.planned_coffee_quantity = planned_coffee_qty
        order.save(update_fields=['items_total_amount', 'discount_amount', 'final_amount',
                                  'planned_use_points', 'planned_points_to_spend',
                                  'planned_earn_points', 'planned_coffee_quantity'])

        return order


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_total_amount_som = serializers.SerializerMethodField()
    final_amount_som = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'coffee_shop', 'delivery_type', 'payment_method', 'payment_status', 'status',
            'items_total_amount', 'discount_amount', 'final_amount',
            'items_total_amount_som', 'final_amount_som',
            'customer_comment', 'delivery_address', 'delivery_latitude', 'delivery_longitude',
            'items', 'created_at'
        ]
        read_only_fields = fields

    def get_items_total_amount_som(self, obj):
        return obj.items_total_amount / 100

    def get_final_amount_som(self, obj):
        return obj.final_amount / 100
