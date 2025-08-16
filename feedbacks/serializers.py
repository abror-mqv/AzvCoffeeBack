from rest_framework import serializers
from .models import Feedback
from core.models import CoffeeShop, User


class FeedbackCreateSerializer(serializers.Serializer):
    coffee_shop_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=Feedback.TYPE_CHOICES)
    text = serializers.CharField(max_length=5000)

    def validate_coffee_shop_id(self, value):
        if not CoffeeShop.objects.filter(id=value).exists():
            raise serializers.ValidationError("Заведение не найдено")
        return value

    def create(self, validated_data):
        request = self.context['request']
        user: User = request.user
        coffee_shop = CoffeeShop.objects.get(id=validated_data['coffee_shop_id'])
        feedback = Feedback.objects.create(
            user=user,
            coffee_shop=coffee_shop,
            type=validated_data['type'],
            text=validated_data['text']
        )
        return feedback


class FeedbackUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'first_name', 'last_name']


class FeedbackListSerializer(serializers.ModelSerializer):
    user = FeedbackUserSerializer(read_only=True)
    coffee_shop = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ['id', 'type', 'text', 'created_at', 'user', 'coffee_shop']

    def get_coffee_shop(self, obj):
        return {
            'id': obj.coffee_shop.id,
            'name': obj.coffee_shop.name,
        }
