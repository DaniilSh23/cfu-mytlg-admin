# Generated by Django 4.2.1 on 2023-07-26 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0022_channels_subscribers_numb'),
    ]

    operations = [
        migrations.AddField(
            model_name='tlgaccounts',
            name='subscribed_numb_of_channels',
            field=models.IntegerField(default=0, verbose_name='кол-во подписок на каналы'),
        ),
    ]