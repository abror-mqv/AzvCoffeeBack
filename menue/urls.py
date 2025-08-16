from django.urls import path
from .views import (
    MenuTreeView, 
    MenuItemListCreateView, 
    MenuItemRetrieveUpdateDestroyView, 
    MenuItemImageUpdateView,
    PortionListCreateView,
    PortionRetrieveUpdateDestroyView,
    ItemVariantListCreateView,
    ItemVariantRetrieveUpdateDestroyView
)

urlpatterns = [
    # Меню и товары
    path('menu-tree/', MenuTreeView.as_view(), name='menu-tree'),
    path('menu-items/', MenuItemListCreateView.as_view(), name='menuitem-list-create'),
    path('menu-items/<int:pk>/', MenuItemRetrieveUpdateDestroyView.as_view(), name='menuitem-detail'),
    path('menu-items/<int:pk>/image/', MenuItemImageUpdateView.as_view(), name='menuitem-image-update'),
    
    # Порции
    path('portions/', PortionListCreateView.as_view(), name='portion-list-create'),
    path('portions/<int:pk>/', PortionRetrieveUpdateDestroyView.as_view(), name='portion-detail'),
    
    # Варианты товаров
    path('menu-items/<int:menu_item_id>/variants/', ItemVariantListCreateView.as_view(), name='item-variant-list-create'),
    path('variants/<int:pk>/', ItemVariantRetrieveUpdateDestroyView.as_view(), name='item-variant-detail'),
] 