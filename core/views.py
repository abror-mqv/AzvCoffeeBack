from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication, generics
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import CoffeeShop, User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    ClientPhoneCheckSerializer, ClientRegistrationSerializer, ClientInfoSerializer,
    CoffeeShopSerializer, WorkingHoursSerializer, ClientListSerializer,
    BaristaLoginSerializer, BaristaInfoSerializer, RankSerializer
)
from django.db import models

UserModel = get_user_model()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@method_decorator(csrf_exempt, name='dispatch')
class ManagerLoginView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')
        user = authenticate(request, phone=phone, password=password)
        if user and user.role == User.ROLE_MANAGER:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Неверные данные или недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_exempt, name='dispatch')
class BaristaLoginView(APIView):
    """
    Авторизация бариста/старшего бариста
    """
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        serializer = BaristaLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(phone=phone, role__in=[User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA])
            
            # Проверяем пароль (т.к. пароль хранится в raw виде)
            if user.password == password:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'phone': user.phone,
                        'role': user.role,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                })
            else:
                return Response({'error': 'Неверный пароль'}, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            return Response({'error': 'Бариста с таким номером не найден'}, status=status.HTTP_404_NOT_FOUND)


class BaristaInfoView(APIView):
    """
    Получение информации о бариста
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]
    
    def get(self, request):
        user = request.user
        
        # Проверяем, что пользователь является бариста или старшим бариста
        if user.role not in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA]:
            return Response({
                'error': 'Доступ только для бариста и старших бариста'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = BaristaInfoSerializer(user)
        return Response(serializer.data)


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ROLE_MANAGER

class BaristaRegisterView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        phone = request.data.get('phone')
        role = request.data.get('role')
        coffee_shop_id = request.data.get('coffee_shop_id')
        password = request.data.get('password')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        if role not in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA]:
            return Response({'error': 'Роль должна быть бариста или старший бариста'}, status=400)
        if not phone or not coffee_shop_id or not password or not first_name or not last_name:
            return Response({'error': 'Необходимы телефон, пароль, имя, фамилия и ID заведения'}, status=400)
        try:
            coffee_shop = CoffeeShop.objects.get(id=coffee_shop_id)
        except CoffeeShop.DoesNotExist:
            return Response({'error': 'Заведение не найдено'}, status=404)
        if User.objects.filter(phone=phone).exists():
            return Response({'error': 'Пользователь с таким телефоном уже существует'}, status=400)
        user = User.objects.create(
            phone=phone,
            role=role,
            coffee_shop=coffee_shop,
            first_name=first_name,
            last_name=last_name
        )
        user.password = password  # raw password, небезопасно, но по требованию
        user.save()
        return Response({'success': f'{user.get_role_display()} создан', 'user_id': user.id})

class CoffeeShopRegisterView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        serializer = CoffeeShopSerializer(data=request.data)
        if serializer.is_valid():
            coffee_shop = serializer.save()
            return Response({
                'success': 'Заведение создано', 
                'coffee_shop_id': coffee_shop.id
            })
        return Response({'error': serializer.errors}, status=400)

class CoffeeShopListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request):
        shops = CoffeeShop.objects.all()
        serializer = CoffeeShopSerializer(shops, many=True)
        return Response(serializer.data)

class BaristaListView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request):
        baristas = User.objects.filter(role__in=[User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA])
        data = []
        for user in baristas:
            data.append({
                'id': user.id,
                'phone': user.phone,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'coffee_shop_id': user.coffee_shop.id if user.coffee_shop else None,
                'coffee_shop_name': user.coffee_shop.name if user.coffee_shop else None,
                'password': user.password  # raw password, как есть
            })
        return Response(data)

class ClientListView(generics.ListAPIView):
    """
    Получение списка всех клиентов с пагинацией
    """
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = ClientListSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = User.objects.filter(role=User.ROLE_CLIENT).order_by('-date_joined')
        
        # Фильтрация по имени, фамилии или телефону
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) | 
                models.Q(last_name__icontains=search) | 
                models.Q(phone__icontains=search)
            )
        
        # Фильтрация по минимальной сумме трат
        min_spent = self.request.query_params.get('min_spent', None)
        if min_spent and min_spent.isdigit():
            queryset = queryset.filter(total_spent__gte=int(min_spent) * 100)  # Переводим в копейки
        
        # Фильтрация по минимальному количеству кофе
        min_coffee = self.request.query_params.get('min_coffee', None)
        if min_coffee and min_coffee.isdigit():
            queryset = queryset.filter(coffee_count__gte=int(min_coffee))
            
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class AssignBaristaView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        barista_id = request.data.get('barista_id')
        coffee_shop_id = request.data.get('coffee_shop_id')
        is_responsible = request.data.get('is_responsible', False)
        if barista_id is None or coffee_shop_id is None:
            return Response({'error': 'Необходимы barista_id и coffee_shop_id'}, status=400)
        try:
            barista = User.objects.get(id=barista_id, role__in=[User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA])
        except User.DoesNotExist:
            return Response({'error': 'Бариста не найден'}, status=404)
        try:
            shop = CoffeeShop.objects.get(id=coffee_shop_id)
        except CoffeeShop.DoesNotExist:
            return Response({'error': 'Заведение не найдено'}, status=404)
        barista.coffee_shop = shop
        barista.save()
        if is_responsible:
            shop.responsible_senior_barista = barista
            shop.save()
        return Response({'success': 'Бариста закреплён за заведением', 'responsible': is_responsible})

class EditBaristaView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        barista_id = request.data.get('barista_id')
        phone = request.data.get('phone')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        role = request.data.get('role')
        password = request.data.get('password')
        if not barista_id:
            return Response({'error': 'Необходим barista_id'}, status=400)
        try:
            user = User.objects.get(id=barista_id, role__in=[User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA])
        except User.DoesNotExist:
            return Response({'error': 'Бариста не найден'}, status=404)
        if phone:
            if User.objects.exclude(id=user.id).filter(phone=phone).exists():
                return Response({'error': 'Пользователь с таким телефоном уже существует'}, status=400)
            user.phone = phone
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if role and role in [User.ROLE_BARISTA, User.ROLE_SENIOR_BARISTA]:
            user.role = role
        if password:
            user.password = password  # raw password, по требованию
        user.save()
        return Response({'success': 'Бариста обновлён'})

class EditCoffeeShopView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        coffee_shop_id = request.data.get('coffee_shop_id')
        if not coffee_shop_id:
            return Response({'error': 'Необходим coffee_shop_id'}, status=400)
        try:
            shop = CoffeeShop.objects.get(id=coffee_shop_id)
        except CoffeeShop.DoesNotExist:
            return Response({'error': 'Заведение не найдено'}, status=404)
        
        serializer = CoffeeShopSerializer(shop, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': 'Заведение обновлено'})
        return Response({'error': serializer.errors}, status=400)

class CoffeeShopWorkingHoursView(APIView):
    permission_classes = [IsManager]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        coffee_shop_id = request.data.get('coffee_shop_id')
        if not coffee_shop_id:
            return Response({'error': 'Необходим coffee_shop_id'}, status=400)
        try:
            shop = CoffeeShop.objects.get(id=coffee_shop_id)
        except CoffeeShop.DoesNotExist:
            return Response({'error': 'Заведение не найдено'}, status=404)
        
        serializer = WorkingHoursSerializer(data=request.data)
        if serializer.is_valid():
            day_of_week = serializer.validated_data['day_of_week']
            opening_time = serializer.validated_data['opening_time']
            closing_time = serializer.validated_data['closing_time']
            
            shop.set_working_hours(day_of_week, opening_time, closing_time)
            
            return Response({
                'success': f'Часы работы для {CoffeeShop.DAYS_OF_WEEK[day_of_week][1]} установлены',
                'day_of_week': day_of_week,
                'opening_time': opening_time,
                'closing_time': closing_time
            })
        return Response({'error': serializer.errors}, status=400)
    
    def get(self, request):
        coffee_shop_id = request.query_params.get('coffee_shop_id')
        if not coffee_shop_id:
            return Response({'error': 'Необходим coffee_shop_id'}, status=400)
        try:
            shop = CoffeeShop.objects.get(id=coffee_shop_id)
        except CoffeeShop.DoesNotExist:
            return Response({'error': 'Заведение не найдено'}, status=404)
        
        day_of_week = request.query_params.get('day_of_week')
        if day_of_week is not None:
            try:
                day_of_week = int(day_of_week)
                if not 0 <= day_of_week <= 6:
                    raise ValueError()
            except (ValueError, TypeError):
                return Response({'error': 'day_of_week должен быть числом от 0 до 6'}, status=400)
            
            hours = shop.get_working_hours(day_of_week)
            return Response({
                'day_of_week': day_of_week,
                'day_name': CoffeeShop.DAYS_OF_WEEK[day_of_week][1],
                'hours': hours
            })
        
        hours = shop.get_working_hours()
        formatted_hours = {}
        for day, times in hours.items():
            day_int = int(day)
            formatted_hours[day] = {
                'day_name': CoffeeShop.DAYS_OF_WEEK[day_int][1],
                'open': times.get('open'),
                'close': times.get('close')
            }
        
        return Response(formatted_hours)


@method_decorator(csrf_exempt, name='dispatch')
class ClientPhoneCheckView(APIView):
    """
    Проверка номера телефона клиента
    Если номер существует и роль = client - авторизуем
    Если номер не существует - возвращаем 200 для регистрации
    Если номер занят другой ролью - возвращаем ошибку
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = ClientPhoneCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone']
        
        try:
            user = User.objects.get(phone=phone)
            
            # Если пользователь существует и это клиент
            if user.role == User.ROLE_CLIENT:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'status': 'authorized',
                    'message': 'Клиент успешно авторизован',
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'phone': user.phone,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'birth_date': user.birth_date,
                        'points': user.points,
                        'coffee_count': user.coffee_count,
                        'total_spent': user.total_spent
                    }
                }, status=status.HTTP_200_OK)
            
            # Если номер занят другой ролью
            else:
                return Response({
                    'status': 'error',
                    'message': 'Номер телефона уже используется в системе'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            # Номер не найден - можно регистрироваться
            return Response({
                'status': 'registration_required',
                'message': 'Номер телефона не найден. Требуется регистрация.'
            }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ClientRegistrationView(APIView):
    """
    Регистрация нового клиента
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = ClientRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'status': 'registered',
                'message': 'Клиент успешно зарегистрирован',
                'token': token.key,
                'user': {
                    'id': user.id,
                    'phone': user.phone,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'birth_date': user.birth_date,
                    'points': user.points,
                    'coffee_count': user.coffee_count,
                    'total_spent': user.total_spent
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Ошибка при регистрации: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientInfoView(APIView):
    """
    Получение информации о клиенте
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request):
        user = request.user
        
        # Проверяем, что пользователь является клиентом
        if user.role != User.ROLE_CLIENT:
            return Response({
                'error': 'Доступ только для клиентов'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ClientInfoSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        """Частичное обновление данных клиента: phone, first_name, last_name"""
        user = request.user
        if user.role != User.ROLE_CLIENT:
            return Response({'error': 'Доступ только для клиентов'}, status=status.HTTP_403_FORBIDDEN)

        phone = request.data.get('phone')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        # Валидация телефона: уникален среди всех, кроме текущего пользователя
        if phone:
            if User.objects.exclude(id=user.id).filter(phone=phone).exists():
                return Response({'error': 'Пользователь с таким телефоном уже существует'}, status=status.HTTP_400_BAD_REQUEST)
            user.phone = phone

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        user.save()
        return Response(ClientInfoSerializer(user).data)

    def put(self, request):
        """Полное обновление (эквивалентно patch для перечисленных полей)"""
        return self.patch(request)


class RanksListView(APIView):
    """Публичный список рангов и их условий."""
    permission_classes = [AllowAny]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request):
        from .models import Rank
        ranks = Rank.objects.all().order_by('min_total_spent_som')
        data = RankSerializer(ranks, many=True, context={'request': request}).data
        return Response(data)
