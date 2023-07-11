# Generated by Django 4.2.1 on 2023-07-11 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0011_channels_sub_theme_alter_channels_theme'),
    ]

    operations = [
        migrations.AddField(
            model_name='botuser',
            name='sub_themes',
            field=models.ManyToManyField(blank=True, related_name='bot_user', to='mytlg.subthemes', verbose_name='подтемы'),
        ),
        migrations.AlterField(
            model_name='botuser',
            name='themes',
            field=models.ManyToManyField(blank=True, related_name='bot_user', to='mytlg.themes', verbose_name='темы'),
        ),
    ]
