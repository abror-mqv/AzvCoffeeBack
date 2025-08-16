from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание категории")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Фото категории")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Portion(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название порции")
    volume = models.PositiveIntegerField(verbose_name="Объём")
    unit = models.CharField(max_length=10, default="мл", verbose_name="Единица измерения")

    def __str__(self):
        return f"{self.name} ({self.volume} {self.unit})"

    class Meta:
        verbose_name = "Порция"
        verbose_name_plural = "Порции"
        unique_together = ("name", "volume", "unit")

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items', verbose_name="Категория")
    name = models.CharField(max_length=100, verbose_name="Название товара")
    description = models.TextField(blank=True, verbose_name="Описание")
    ingredients = models.TextField(blank=True, verbose_name="Состав")
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True, verbose_name="Фото")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Позиция меню"
        verbose_name_plural = "Позиции меню"

class ItemVariant(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='variants', verbose_name="Товар")
    portion = models.ForeignKey(Portion, on_delete=models.CASCADE, related_name='item_variants', verbose_name="Порция")
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Цена")
    is_default = models.BooleanField(default=False, verbose_name="Вариант по умолчанию")

    def __str__(self):
        return f"{self.menu_item.name} - {self.portion}"

    class Meta:
        verbose_name = "Вариант товара"
        verbose_name_plural = "Варианты товаров"
        unique_together = ("menu_item", "portion")
