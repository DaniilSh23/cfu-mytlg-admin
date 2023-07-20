# Generated by Django 4.2.1 on 2023-07-19 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0013_themesweight'),
    ]

    operations = [
        migrations.CreateModel(
            name='TlgAccounts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_file', models.FileField(null=True, upload_to='sessions/', verbose_name='файл сессии')),
                ('acc_tlg_id', models.CharField(blank=True, max_length=50, verbose_name='tlg_id аккаунта')),
                ('tlg_first_name', models.CharField(blank=True, max_length=50, verbose_name='tlg_first_name')),
                ('tlg_last_name', models.CharField(blank=True, max_length=50, verbose_name='tlg_last_name')),
                ('proxy', models.CharField(blank=True, max_length=200, verbose_name='proxy')),
                ('is_run', models.BooleanField(default=False, verbose_name='аккаунт запущен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='дата и время добавления акка')),
            ],
            options={
                'verbose_name': 'tlg аккаунт',
                'verbose_name_plural': 'tlg аккаунты',
                'ordering': ['-id'],
            },
        ),
    ]