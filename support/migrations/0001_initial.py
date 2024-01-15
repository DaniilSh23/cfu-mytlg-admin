# Generated by Django 4.2.1 on 2024-01-12 13:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mytlg', '0064_botuser_is_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportMessages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(blank=True, verbose_name='Сообщение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')),
                ('bot_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mytlg.botuser', verbose_name='Пользователь бота')),
            ],
        ),
    ]