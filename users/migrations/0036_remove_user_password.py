# Generated by Django 4.2.6 on 2024-01-24 11:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0035_reportusers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='password',
        ),
    ]
