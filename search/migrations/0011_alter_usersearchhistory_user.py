# Generated by Django 4.2.6 on 2024-03-17 07:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0062_notifications_is_seen'),
        ('search', '0010_usersearchhistory_delete_usersearchpreferences'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersearchhistory',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='searchhistory', to='users.user'),
        ),
    ]
