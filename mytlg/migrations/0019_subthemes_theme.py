# Generated by Django 4.2.1 on 2023-07-20 15:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0018_newsposts'),
    ]

    operations = [
        migrations.AddField(
            model_name='subthemes',
            name='theme',
            field=models.ForeignKey(blank=True, default=75, on_delete=django.db.models.deletion.CASCADE, to='mytlg.themes', verbose_name='связанная тема'),
            preserve_default=False,
        ),
    ]
