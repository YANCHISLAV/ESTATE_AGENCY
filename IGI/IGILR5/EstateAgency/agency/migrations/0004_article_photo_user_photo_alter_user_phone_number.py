# Generated by Django 5.2.1 on 2025-05-30 13:11

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0003_remove_user_photo_alter_user_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='news_photos'),
        ),
        migrations.AddField(
            model_name='user',
            name='photo',
            field=models.ImageField(default='avatars/default_avatar.png', upload_to='avatars'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+375(29)XXXXXX'", regex='^\\+375\\)?\\((29|33|25)\\)\\d{7}$')]),
        ),
    ]
