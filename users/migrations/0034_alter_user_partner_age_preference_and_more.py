# Generated by Django 4.2.6 on 2024-01-24 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_user_password_user_whatsapp_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='partner_age_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner age preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_caste_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner caste preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_cities_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner cities preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_country_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner country preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_expertise_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner expertise preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_graduation_preference',
            field=models.BooleanField(default=False, help_text='If False then no graduation preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_height_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner height preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_marital_status_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner marital status preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_postgraduation_preference',
            field=models.BooleanField(default=False, help_text='If False then no postgrad preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_religion_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner religion preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_specialization_preference',
            field=models.BooleanField(default=False, help_text='If False then no specialization preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_state_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner state preference'),
        ),
    ]
