# Generated by Django 4.2.6 on 2023-12-27 04:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_viewedstories'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='activity_status',
            field=models.BooleanField(default=False),
        ),
    ]
