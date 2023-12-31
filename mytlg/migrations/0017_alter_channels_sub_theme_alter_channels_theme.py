# Generated by Django 4.2.1 on 2023-07-20 10:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0016_alter_botsettings_options_alter_channels_sub_theme_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channels',
            name='sub_theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mytlg.subthemes', verbose_name='подтема канала'),
        ),
        migrations.AlterField(
            model_name='channels',
            name='theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mytlg.themes', verbose_name='тема канала'),
        ),
    ]
