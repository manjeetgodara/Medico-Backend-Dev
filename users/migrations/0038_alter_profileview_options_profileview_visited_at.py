# Generated by Django 4.2.6 on 2024-01-25 05:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0037_user_password'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profileview',
            options={'ordering': ['-visited_at']},
        ),
        migrations.AddField(
            model_name='profileview',
            name='visited_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
