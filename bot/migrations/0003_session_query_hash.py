# Generated by Django 3.1.4 on 2020-12-17 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_session_telegram_photo_file_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='query_hash',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]