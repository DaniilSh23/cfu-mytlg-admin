# Generated by Django 4.2.1 on 2023-09-19 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0043_alter_scheduledposts_is_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsposts',
            name='short_text',
            field=models.TextField(blank=True, null=True, verbose_name='краткий текст'),
        ),
    ]
