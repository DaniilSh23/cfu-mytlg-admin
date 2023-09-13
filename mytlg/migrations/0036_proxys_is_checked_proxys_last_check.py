# Generated by Django 4.2.1 on 2023-09-13 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0035_proxys'),
    ]

    operations = [
        migrations.AddField(
            model_name='proxys',
            name='is_checked',
            field=models.BooleanField(default=False, verbose_name='проверена'),
        ),
        migrations.AddField(
            model_name='proxys',
            name='last_check',
            field=models.DateTimeField(blank=True, null=True, verbose_name='крайняя проверка'),
        ),
    ]
