# Generated by Django 4.2.1 on 2023-12-14 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0061_botuser_only_custom_channels'),
    ]

    operations = [
        migrations.AddField(
            model_name='channels',
            name='is_blocked',
            field=models.BooleanField(default=False, verbose_name='Канал заблокирован'),
        ),
    ]