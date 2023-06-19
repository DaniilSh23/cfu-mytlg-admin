# Generated by Django 4.2.1 on 2023-06-19 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0006_alter_channels_options_alter_themes_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='botuser',
            name='channels',
            field=models.ManyToManyField(related_name='bot_user', to='mytlg.channels', verbose_name='каналы'),
        ),
        migrations.AlterField(
            model_name='channels',
            name='channel_id',
            field=models.CharField(blank=True, max_length=50, verbose_name='ID канала'),
        ),
    ]
