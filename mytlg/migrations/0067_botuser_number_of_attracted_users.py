# Generated by Django 4.2.1 on 2024-01-29 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0066_botuser_share_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='botuser',
            name='number_of_attracted_users',
            field=models.IntegerField(default=0, verbose_name='Количество привлеченных пользователей'),
        ),
    ]