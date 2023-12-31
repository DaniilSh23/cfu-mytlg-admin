# Generated by Django 4.2.1 on 2023-07-11 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0009_botuser_when_send_news'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubThemes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sub_theme_name', models.CharField(max_length=200, verbose_name='имя подтмемы')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='дата и время создания')),
            ],
            options={
                'verbose_name': 'подтема',
                'verbose_name_plural': 'подтемы',
                'ordering': ['id'],
            },
        ),
        migrations.AlterModelOptions(
            name='themes',
            options={'ordering': ['id'], 'verbose_name': 'тема', 'verbose_name_plural': 'темы'},
        ),
        migrations.AlterField(
            model_name='themes',
            name='theme_name',
            field=models.CharField(max_length=200, verbose_name='имя темы'),
        ),
    ]
