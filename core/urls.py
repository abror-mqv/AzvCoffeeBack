from django.urls import path
from .views import (
    ManagerLoginView, BaristaRegisterView, CoffeeShopRegisterView, 
    CoffeeShopListView, BaristaListView, AssignBaristaView, 
    EditBaristaView, EditCoffeeShopView, ClientPhoneCheckView, 
    ClientRegistrationView, ClientInfoView, CoffeeShopWorkingHoursView,
    ClientListView, BaristaLoginView, BaristaInfoView, RanksListView
)

urlpatterns = [
    path('manager/login/', ManagerLoginView.as_view(), name='manager-login'),
    path('manager/register-barista/', BaristaRegisterView.as_view(), name='register-barista'),
    path('manager/register-coffeeshop/', CoffeeShopRegisterView.as_view(), name='register-coffeeshop'),
    path('coffeeshops/', CoffeeShopListView.as_view(), name='coffeeshop-list'),
    path('baristas/', BaristaListView.as_view(), name='barista-list'),
    path('clients/', ClientListView.as_view(), name='client-list'),  # Новый маршрут для списка клиентов
    path('assign-barista/', AssignBaristaView.as_view(), name='assign-barista'),
    path('edit-barista/', EditBaristaView.as_view(), name='edit-barista'),
    path('edit-coffeeshop/', EditCoffeeShopView.as_view(), name='edit-coffeeshop'),
    
    # Новые эндпоинты для рабочих часов
    path('coffeeshop/working-hours/', CoffeeShopWorkingHoursView.as_view(), name='coffeeshop-working-hours'),
    
    # Эндпоинты для бариста
    path('barista/login/', BaristaLoginView.as_view(), name='barista-login'),
    path('barista/info/', BaristaInfoView.as_view(), name='barista-info'),
    
    # Клиентские endpoints
    path('client/check-phone/', ClientPhoneCheckView.as_view(), name='client-check-phone'),
    path('client/register/', ClientRegistrationView.as_view(), name='client-register'),
    path('client/info/', ClientInfoView.as_view(), name='client-info'),
    path('ranks/', RanksListView.as_view(), name='ranks-list'),
] 