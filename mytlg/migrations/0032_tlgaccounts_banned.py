# Generated by Django 4.2.1 on 2023-09-10 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0031_categories_remove_themesweight_bot_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tlgaccounts',
            name='banned',
            field=models.BooleanField(default=False, verbose_name='забанен'),
        ),
    ]