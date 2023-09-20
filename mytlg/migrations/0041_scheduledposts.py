# Generated by Django 4.2.1 on 2023-09-18 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mytlg', '0040_alter_interests_send_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledPosts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when_send', models.DateTimeField(verbose_name='когда отправить')),
                ('is_sent', models.BooleanField(verbose_name='отправлено')),
                ('bot_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mytlg.botuser', verbose_name='юзер бота')),
                ('news_post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mytlg.newsposts', verbose_name='пост')),
            ],
            options={
                'verbose_name': 'запланированный пост',
                'verbose_name_plural': 'запланированные посты',
                'ordering': ['-id'],
            },
        ),
    ]
