from django.shortcuts import render
from rest_framework import generics, permissions, authentication, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import MenuItem, Category, Portion, ItemVariant
from .serializers import MenuItemSerializer, CategorySerializer, PortionSerializer, ItemVariantSerializer
from core.views import IsManager

# Create your views here.

# CRUD для управляющего
class MenuItemListCreateView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

class MenuItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

# Древовидный вывод: категории с вложенными товарами
class MenuTreeView(generics.GenericAPIView):
    # Публичный доступ
    def get(self, request):
        categories = Category.objects.all()
        data = []
        for cat in categories:
            items = MenuItem.objects.filter(category=cat)
            items_ser = MenuItemSerializer(items, many=True, context={'request': request}).data
            cat_ser = CategorySerializer(cat, context={'request': request}).data
            cat_ser['items'] = items_ser
            data.append(cat_ser)
        return Response(data)

class MenuItemImageUpdateView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def patch(self, request, pk):
        try:
            item = MenuItem.objects.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({'error': 'Позиция не найдена'}, status=status.HTTP_404_NOT_FOUND)
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'Необходимо передать файл image'}, status=status.HTTP_400_BAD_REQUEST)
        item.image = image
        item.save()
        return Response(MenuItemSerializer(item, context={'request': request}).data)

# CRUD для порций
class PortionListCreateView(generics.ListCreateAPIView):
    queryset = Portion.objects.all()
    serializer_class = PortionSerializer
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

class PortionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Portion.objects.all()
    serializer_class = PortionSerializer
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

# CRUD для вариантов товаров
class ItemVariantListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemVariantSerializer
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]
    
    def get_queryset(self):
        menu_item_id = self.kwargs.get('menu_item_id')
        return ItemVariant.objects.filter(menu_item_id=menu_item_id)
    
    def perform_create(self, serializer):
        menu_item_id = self.kwargs.get('menu_item_id')
        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
            serializer.save(menu_item=menu_item)
        except MenuItem.DoesNotExist:
            pass

class ItemVariantRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ItemVariant.objects.all()
    serializer_class = ItemVariantSerializer
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]
