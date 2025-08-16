from rest_framework import serializers
from .models import Category, MenuItem, Portion, ItemVariant

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class PortionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portion
        fields = ['id', 'name', 'volume', 'unit']

class ItemVariantSerializer(serializers.ModelSerializer):
    portion = PortionSerializer(read_only=True)
    portion_id = serializers.PrimaryKeyRelatedField(queryset=Portion.objects.all(), source='portion', write_only=True)

    class Meta:
        model = ItemVariant
        fields = ['id', 'portion', 'portion_id', 'price', 'is_default']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)
    image = serializers.SerializerMethodField()
    variants = ItemVariantSerializer(many=True, read_only=True)
    
    # Для совместимости с API документацией
    volume = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_id', 'name', 'description', 'ingredients', 'image',
            'variants', 'volume', 'price', 'is_active', 'created_at', 'updated_at'
        ]

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_volume(self, obj):
        # Возвращает объем варианта по умолчанию для обратной совместимости
        default_variant = obj.variants.filter(is_default=True).first()
        if default_variant:
            portion = default_variant.portion
            return f"{portion.volume} {portion.unit}"
        return None
    
    def get_price(self, obj):
        # Возвращает цену варианта по умолчанию для обратной совместимости
        default_variant = obj.variants.filter(is_default=True).first()
        if default_variant:
            return default_variant.price
        return None
    
    def create(self, validated_data):
        # Извлекаем данные вариантов из запроса
        variants_data = self.context['request'].data.get('variants', [])
        
        # Создаем MenuItem
        menu_item = MenuItem.objects.create(**validated_data)
        
        # Создаем варианты для товара
        for variant_data in variants_data:
            portion_id = variant_data.get('portion_id')
            price = variant_data.get('price')
            is_default = variant_data.get('is_default', False)
            
            if portion_id and price:
                try:
                    portion = Portion.objects.get(id=portion_id)
                    ItemVariant.objects.create(
                        menu_item=menu_item,
                        portion=portion,
                        price=price,
                        is_default=is_default
                    )
                except Portion.DoesNotExist:
                    pass
        
        return menu_item
    
    def update(self, instance, validated_data):
        # Обновляем базовые поля MenuItem
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем варианты, если они предоставлены
        variants_data = self.context['request'].data.get('variants')
        if variants_data is not None:
            # Обработка обновления вариантов
            current_variants = {variant.id: variant for variant in instance.variants.all()}
            
            for variant_data in variants_data:
                variant_id = variant_data.get('id')
                
                if variant_id and variant_id in current_variants:
                    # Обновляем существующий вариант
                    variant = current_variants[variant_id]
                    if 'portion_id' in variant_data:
                        try:
                            variant.portion = Portion.objects.get(id=variant_data['portion_id'])
                        except Portion.DoesNotExist:
                            pass
                    if 'price' in variant_data:
                        variant.price = variant_data['price']
                    if 'is_default' in variant_data:
                        variant.is_default = variant_data['is_default']
                    variant.save()
                elif not variant_id:
                    # Создаем новый вариант
                    portion_id = variant_data.get('portion_id')
                    price = variant_data.get('price')
                    is_default = variant_data.get('is_default', False)
                    
                    if portion_id and price:
                        try:
                            portion = Portion.objects.get(id=portion_id)
                            ItemVariant.objects.create(
                                menu_item=instance,
                                portion=portion,
                                price=price,
                                is_default=is_default
                            )
                        except Portion.DoesNotExist:
                            pass
        
        return instance 