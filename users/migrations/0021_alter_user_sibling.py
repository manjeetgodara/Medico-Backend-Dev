# Generated by Django 4.2.6 on 2024-01-04 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_alter_user_beauty_consciousness_alter_user_foodie_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='sibling',
            field=models.BooleanField(blank=True, help_text='Indicates whether user has siblings or not', null=True),
        ),
    ]
