# Generated by Django 4.2.1 on 2023-06-14 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BotUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tlg_id', models.CharField(db_index=True, max_length=30, verbose_name='tlg_id')),
                ('tlg_username', models.CharField(max_length=100, null=True, verbose_name='username')),
                ('start_bot_at', models.DateTimeField(auto_now_add=True, verbose_name='первый старт')),
            ],
            options={
                'verbose_name': 'юзер бота',
                'verbose_name_plural': 'юзеры бота',
                'ordering': ['-start_bot_at'],
            },
        ),
    ]
