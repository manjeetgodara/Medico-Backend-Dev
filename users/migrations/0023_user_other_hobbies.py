# Generated by Django 4.2.6 on 2024-01-05 05:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_merge_0017_successstory_0021_alter_user_sibling'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='other_hobbies',
            field=models.TextField(default='[]'),
        ),
    ]
