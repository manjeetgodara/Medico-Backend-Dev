# Generated by Django 4.2.6 on 2024-05-22 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0067_deleteprofile_successstory_experience_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppleSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=500)),
                ('description', models.TextField()),
                ('regular_plan', models.BooleanField(default=True)),
                ('timeframe', models.PositiveSmallIntegerField()),
                ('amount', models.PositiveIntegerField()),
            ],
        ),
    ]
