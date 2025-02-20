# Generated by Django 4.2.6 on 2023-12-06 05:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_subscription_usersubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkedaccount',
            name='phone_is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='linkedaccount',
            name='preferred_time_connect',
            field=models.CharField(blank=True, help_text='Indicates preferred time for connect', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='eyesight',
            field=models.CharField(blank=True, help_text='Indicates your eyesight', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='preferred_time_connect',
            field=models.CharField(blank=True, help_text='Indicates preferred time for connect', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usersubscription', to='users.user'),
        ),
    ]
