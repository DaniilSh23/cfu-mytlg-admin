# Generated by Django 4.2.1 on 2023-09-25 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0049_blacklists'),
    ]

    operations = [
        migrations.AddField(
            model_name='botuser',
            name='language_code',
            field=models.CharField(default='RU', max_length=5, verbose_name='language_code'),
        ),
    ]
