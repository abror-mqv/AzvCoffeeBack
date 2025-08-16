from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, authentication
from rest_framework.permissions import IsAuthenticated

from core.models import User
from .serializers import FeedbackCreateSerializer, FeedbackListSerializer
from .models import Feedback


class FeedbackCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        # Только клиенты могут оставлять отзывы
        if request.user.role != User.ROLE_CLIENT:
            return Response({'error': 'Доступ только для клиентов'}, status=status.HTTP_403_FORBIDDEN)

        serializer = FeedbackCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()
        return Response({'success': 'Отзыв сохранён', 'id': feedback.id}, status=status.HTTP_201_CREATED)


class FeedbackListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request):
        # Только управляющий видит список отзывов
        if request.user.role != User.ROLE_MANAGER:
            return Response({'error': 'Доступ только для управляющего'}, status=status.HTTP_403_FORBIDDEN)

        # Фильтрация по заведению (опционально)
        coffee_shop_id = request.query_params.get('coffee_shop_id')
        type_param = request.query_params.get('type')  # 'idea' | 'service'
        qs = Feedback.objects.all().select_related('user', 'coffee_shop').order_by('-created_at')
        if coffee_shop_id:
            qs = qs.filter(coffee_shop_id=coffee_shop_id)
        if type_param:
            qs = qs.filter(type=type_param)

        data = FeedbackListSerializer(qs, many=True).data
        return Response(data)
