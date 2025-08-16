from rest_framework import generics, permissions, status, authentication
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer
from core.models import User


class OrderCreateView(generics.CreateAPIView):
    """Клиент создаёт заказ из готовой корзины"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = OrderCreateSerializer

    def create(self, request, *args, **kwargs):
        print(request.data)
        if request.user.role not in [User.ROLE_CLIENT, User.ROLE_ANON_CLIENT]:
            return Response({"error": "Только клиенты могут создавать заказы"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """Список заказов: клиент видит свои; бариста/старший бариста видят заказы своего заведения"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ROLE_CLIENT:
            return Order.objects.filter(user=user).order_by('-created_at')
        if (user.role in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA] and user.coffee_shop):
            return Order.objects.filter(coffee_shop=user.coffee_shop).order_by('-created_at')
        if user.role == User.ROLE_MANAGER:
            return Order.objects.all().order_by('-created_at')
        return Order.objects.none()


class OrderAcceptView(generics.UpdateAPIView):
    """Бариста принимает заказ (меняет статус new -> accepted)"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def update(self, request, *args, **kwargs):
        user = request.user
        if user.role not in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA] or not user.coffee_shop:
            return Response({"error": "Доступ запрещен"}, status=status.HTTP_403_FORBIDDEN)
        order = self.get_object()
        if order.coffee_shop_id != user.coffee_shop_id:
            return Response({"error": "Можно управлять только заказами своего заведения"}, status=status.HTTP_403_FORBIDDEN)
        if order.status != Order.Status.NEW:
            return Response({"error": "Заказ не в статусе 'Новый'"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.ACCEPTED
        order.save(update_fields=['status'])

        # Apply planned loyalty effects only upon acceptance
        if order.user:
            u = order.user
            # Spend points
            if order.planned_use_points and order.planned_points_to_spend > 0:
                u.points = max(0, u.points - order.planned_points_to_spend)
            # Earn points by rank-based percent calculated at order creation
            if order.planned_earn_points > 0:
                u.points += order.planned_earn_points
            # Coffee quantity increment
            if order.planned_coffee_quantity > 0:
                u.coffee_count += order.planned_coffee_quantity
            # Increase total_spent by actually payable amount (kopecks)
            u.total_spent += order.final_amount
            u.save(update_fields=['points', 'coffee_count', 'total_spent'])
        return Response(OrderSerializer(order).data)


# Create your views here.
