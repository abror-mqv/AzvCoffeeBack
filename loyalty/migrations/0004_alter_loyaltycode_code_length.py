from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('loyalty', '0003_remove_loyaltytransaction_points_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loyaltycode',
            name='code',
            field=models.CharField(max_length=8, unique=True, verbose_name='Код лояльности'),
        ),
    ]
