# Generated by Django 4.2.6 on 2024-01-04 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_alter_user_beauty_consciousness_alter_user_foodie_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='manglik',
            field=models.BooleanField(help_text='If true means you state you are manglik', null=True),
        ),
    ]
