from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from colorfield.fields import ColorField

# Create your models here.

class CoffeeShop(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Название заведения")
    address = models.CharField(max_length=512, verbose_name="Адрес")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Долгота")
    opening_hours = models.JSONField(null=True, blank=True, verbose_name="Часы работы", 
                                     help_text="Формат: {'0': {'open': '09:00', 'close': '22:00'}, ...}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responsible_senior_barista = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_shops',
        limit_choices_to={'role': 'senior_barista'},
        verbose_name="Ответственный старший бариста"
    )

    def __str__(self):
        return self.name
    
    def set_working_hours(self, day_of_week, opening_time, closing_time):
        """
        Устанавливает часы работы для конкретного дня недели
        
        Args:
            day_of_week (int): День недели (0-6, где 0 - понедельник)
            opening_time (str): Время открытия в формате 'HH:MM'
            closing_time (str): Время закрытия в формате 'HH:MM'
        """
        if not self.opening_hours:
            self.opening_hours = {}
        
        self.opening_hours[str(day_of_week)] = {
            'open': opening_time,
            'close': closing_time
        }
        self.save()
    
    def get_working_hours(self, day_of_week=None):
        """
        Возвращает часы работы для конкретного дня или для всех дней
        
        Args:
            day_of_week (int, optional): День недели (0-6, где 0 - понедельник)
            
        Returns:
            dict: Часы работы
        """
        if not self.opening_hours:
            return {}
        
        if day_of_week is not None:
            return self.opening_hours.get(str(day_of_week), {})
        
        return self.opening_hours

class UserManager(BaseUserManager):
    def create_user(self, phone, role, password=None, **extra_fields):
        if not phone:
            raise ValueError('Необходимо указать номер телефона')
        user = self.model(phone=phone, role=role, **extra_fields)
        if role == User.ROLE_MANAGER and password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, role='manager', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, role, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_MANAGER = 'manager'
    ROLE_BARISTA = 'barista'
    ROLE_SENIOR_BARISTA = 'senior_barista'
    ROLE_CLIENT = 'client'
    ROLE_ANON_CLIENT = 'anon_client'

    ROLE_CHOICES = [
        (ROLE_MANAGER, 'Управляющий'),
        (ROLE_BARISTA, 'Бариста'),
        (ROLE_SENIOR_BARISTA, 'Старший бариста'),
        (ROLE_CLIENT, 'Клиент'),
        (ROLE_ANON_CLIENT, 'Анонимный клиент'),
    ]

    phone = models.CharField(max_length=20, unique=True, verbose_name="Телефон")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Роль")
    coffee_shop = models.ForeignKey(
        CoffeeShop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
        verbose_name="Заведение",
        help_text="Только для бариста и старших бариста"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=50, verbose_name="Имя", blank=True, null=True)
    last_name = models.CharField(max_length=50, verbose_name="Фамилия", blank=True, null=True)
    birth_date = models.DateField(verbose_name="Дата рождения", blank=True, null=True)
    
    # Поля для клиентов
    points = models.IntegerField(default=0, verbose_name="Баллы")
    coffee_count = models.IntegerField(default=0, verbose_name="Количество кофе")
    total_spent = models.IntegerField(default=0, verbose_name="Общий чек (в копейках)")

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['role']

    objects = UserManager()

    def __str__(self):
        return f"{self.get_role_display()} {self.phone}"

    def add_points(self, points_to_add):
        """Добавить баллы клиенту"""
        if self.role == self.ROLE_CLIENT:
            self.points += points_to_add
            self.save()
            return True
        return False



    def get_free_coffee_count(self):
        """Получить количество бесплатных кофе (каждое 7-е кофе бесплатно)"""
        if self.role == self.ROLE_CLIENT:
            return self.coffee_count // 7
        return 0

    def get_coffee_to_next_free(self):
        """Получить количество кофе до следующего бесплатного"""
        if self.role == self.ROLE_CLIENT:
            return 7 - (self.coffee_count % 7)
        return 0

    def get_total_spent_rubles(self):
        """Получить общий чек в рублях"""
        return self.total_spent / 100

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Rank(models.Model):
    """Ранг клиента по суммарным тратам (в сомах). Управляется из админки."""
    name = models.CharField(max_length=100, verbose_name='Название ранга')
    min_total_spent_som = models.IntegerField(verbose_name='Минимальная сумма, сом')
    cashback_percent = models.IntegerField(verbose_name='Кэшбек, %')
    icon = models.ImageField(upload_to='ranks/', blank=True, null=True, verbose_name='Иконка')
    color = ColorField(default="#000000", blank=True, verbose_name='Цвет ранга (HEX)')

    class Meta:
        ordering = ['min_total_spent_som']
        verbose_name = 'Ранг'
        verbose_name_plural = 'Ранги'

    def __str__(self):
        return f"{self.name} ({self.cashback_percent}%)"

    @classmethod
    def get_current_for_total_spent(cls, total_spent_kop: int):
        """Возвращает текущий ранг для переданной суммы трат в копейках."""
        total_spent_som = (total_spent_kop or 0) // 100
        ranks = list(cls.objects.all().order_by('min_total_spent_som'))
        current = None
        for r in ranks:
            if total_spent_som >= r.min_total_spent_som:
                current = r
            else:
                break
        return current

    @classmethod
    def get_next_after(cls, rank):
        if not rank:
            # Если ранга ещё нет, вернуть минимальный как следующий
            return cls.objects.all().order_by('min_total_spent_som').first()
        return cls.objects.filter(min_total_spent_som__gt=rank.min_total_spent_som).order_by('min_total_spent_som').first()

    @classmethod
    def get_progress_percent(cls, total_spent_kop: int):
        """Возвращает (current_rank, next_rank, progress_percent 1..100)."""
        total_spent_som = (total_spent_kop or 0) // 100
        current = cls.get_current_for_total_spent(total_spent_kop)
        next_rank = cls.get_next_after(current) if current else cls.get_next_after(None)
        if not current and next_rank:
            # До первого ранга
            distance = max(1, next_rank.min_total_spent_som)
            progress = int(round((total_spent_som / distance) * 100))
        elif current and next_rank:
            base = current.min_total_spent_som
            distance = max(1, next_rank.min_total_spent_som - base)
            progress = int(round(((total_spent_som - base) / distance) * 100))
        else:
            # На максимальном ранге
            progress = 100
        progress = max(1, min(100, progress))
        return current, next_rank, progress
