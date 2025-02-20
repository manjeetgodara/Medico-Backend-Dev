# Generated by Django 4.2.6 on 2024-03-13 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0058_alter_user_about_alter_user_family_photos_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='about',
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='beauty_consciousness',
            field=models.IntegerField(blank=True, default=-1, help_text='If true you are a conscious about beauty/body', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='body_clock',
            field=models.CharField(blank=True, help_text='Indicates whether you are a morning/latenight person', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='can_upgrade_subscription',
            field=models.IntegerField(default=-1, help_text='This indicates if user can upgrade their current subscription or not, -1 for no subcription, 1 for can upgrade and 0 for not able to upgrade'),
        ),
        migrations.AlterField(
            model_name='user',
            name='city_parents',
            field=models.CharField(blank=True, help_text='City where parents reside', max_length=550, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='completed_post_grad',
            field=models.BooleanField(default=True, help_text='if False then no postgraduation done by user'),
        ),
        migrations.AlterField(
            model_name='user',
            name='eyesight',
            field=models.CharField(blank=True, help_text='Indicates your eyesight', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='facebook_profile',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_car',
            field=models.CharField(blank=True, help_text='Family owns a car', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_environment',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_financial_status',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_house',
            field=models.CharField(blank=True, help_text='Whether house is owned or rented', max_length=550, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_photos',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='father_education',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='father_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='father_occupation',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='foodie',
            field=models.IntegerField(blank=True, default=-1, help_text='If true you are a foodie', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='future_aspirations',
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='hobbies',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='instagram_profile',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='interest_music',
            field=models.CharField(blank=True, help_text='Indicates whether an art lover/music enthusiast', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='interest_party',
            field=models.CharField(blank=True, help_text='Indicates whether candidate loves dining or partying', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='kids_choice',
            field=models.CharField(blank=True, help_text='Indicates your preference on kids', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='linkedin_profile',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mother_education',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mother_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mother_occupation',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='nature',
            field=models.CharField(blank=True, help_text='Indicates your nature', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='notification_token',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='other_hobbies',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='own_car',
            field=models.CharField(blank=True, help_text='Candidate owns a car', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_age_from',
            field=models.PositiveIntegerField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_age_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner age preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_age_to',
            field=models.PositiveIntegerField(default=None, null=True),
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
            name='partner_height_from',
            field=models.PositiveIntegerField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_height_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner height preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_height_to',
            field=models.PositiveIntegerField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_income_from',
            field=models.PositiveIntegerField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_income_to',
            field=models.PositiveIntegerField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_marital_status_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner marital status preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_mothertongue_from',
            field=models.ManyToManyField(blank=True, related_name='partner_mothertongue', to='users.mothertongue'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_mothertongue_preference',
            field=models.BooleanField(default=False, help_text='If False then no partner mother tongue preference'),
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
        migrations.AlterField(
            model_name='user',
            name='phone_is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='preferred_time_connect',
            field=models.CharField(blank=True, help_text='Indicates preferred time for connect', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='profession',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='profession_description',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_pictures',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='registration_number',
            field=models.CharField(blank=True, help_text="Indicates your doctor's registartion number", max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='religious_practices',
            field=models.CharField(blank=True, help_text='Indicates religious practice of candidates', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='residence',
            field=models.CharField(blank=True, help_text='Indicates whether residence is owned or rented', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='schooling_details',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='sibling',
            field=models.IntegerField(blank=True, default=-1, help_text='Indicates whether user has siblings or not', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='time_birth',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='video',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='work_out',
            field=models.IntegerField(blank=True, default=-1, help_text='If true you are a interested in yogs/gym/workout', null=True),
        ),
    ]
