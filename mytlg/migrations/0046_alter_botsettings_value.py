# Generated by Django 4.2.1 on 2023-09-19 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0045_newsposts_post_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botsettings',
            name='value',
            field=models.TextField(verbose_name='значение'),
        ),
    ]
