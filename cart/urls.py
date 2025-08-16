from django.urls import path
from .views import OrderCreateView, OrderListView, OrderAcceptView

urlpatterns = [
    path('cart/orders/', OrderCreateView.as_view(), name='order-create'),
    path('cart/orders/list/', OrderListView.as_view(), name='order-list'),
    path('cart/orders/<int:pk>/accept/', OrderAcceptView.as_view(), name='order-accept'),
]
