# Generated by Django 4.2.6 on 2024-03-13 12:44

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0059_alter_user_about_alter_user_beauty_consciousness_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bacheloroftheday',
            name='religion',
            field=models.CharField(db_index=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='blockedusers',
            name='updated_date',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='caste',
            name='name',
            field=models.CharField(db_index=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='expertise',
            name='name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='graduation',
            name='name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='intrest',
            name='status',
            field=models.CharField(db_index=True, default='Pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='intrest',
            name='updated_date',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='languages',
            name='name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='linkedaccount',
            name='relation',
            field=models.CharField(choices=[('son', 'SON'), ('daughter', 'DAUGHTER'), ('sibling', 'SIBLING'), ('relative', 'RELATIVE'), ('friend', 'FRIEND')], db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='maritalstatus',
            name='name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='mothertongue',
            name='name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='notifications',
            name='message',
            field=models.CharField(blank=True, db_index=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='notifications',
            name='type',
            field=models.CharField(blank=True, db_index=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='postgraduation',
            name='name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='profileview',
            name='viewed_at',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='profileview',
            name='visited_at',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='religion',
            name='name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='reportusers',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='reportusers',
            name='reason',
            field=models.TextField(blank=True, db_index=True, default='[]', null=True),
        ),
        migrations.AlterField(
            model_name='reportusers',
            name='updated_date',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='saveduser',
            name='updated_date',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='specialization',
            name='name',
            field=models.CharField(db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='subcaste',
            name='name',
            field=models.CharField(db_index=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='name',
            field=models.CharField(db_index=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='successstory',
            name='image',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='successstory',
            name='partner_mobile_number',
            field=models.CharField(db_index=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='successstory',
            name='partner_name',
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='successstory',
            name='video',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='beauty_consciousness',
            field=models.IntegerField(blank=True, db_index=True, default=-1, help_text='If true you are a conscious about beauty/body', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='body_clock',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates whether you are a morning/latenight person', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='can_upgrade_subscription',
            field=models.IntegerField(db_index=True, default=-1, help_text='This indicates if user can upgrade their current subscription or not, -1 for no subcription, 1 for can upgrade and 0 for not able to upgrade'),
        ),
        migrations.AlterField(
            model_name='user',
            name='city_parents',
            field=models.CharField(blank=True, db_index=True, help_text='City where parents reside', max_length=550, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='completed_post_grad',
            field=models.BooleanField(db_index=True, default=True, help_text='if False then no postgraduation done by user'),
        ),
        migrations.AlterField(
            model_name='user',
            name='eyesight',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates your eyesight', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='facebook_profile',
            field=models.CharField(blank=True, db_index=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_car',
            field=models.CharField(blank=True, db_index=True, help_text='Family owns a car', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_environment',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_financial_status',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='family_house',
            field=models.CharField(blank=True, db_index=True, help_text='Whether house is owned or rented', max_length=550, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='father_education',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='father_name',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='father_occupation',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='foodie',
            field=models.IntegerField(blank=True, db_index=True, default=-1, help_text='If true you are a foodie', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='instagram_profile',
            field=models.CharField(blank=True, db_index=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='interest_music',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates whether an art lover/music enthusiast', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='interest_party',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates whether candidate loves dining or partying', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='kids_choice',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates your preference on kids', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='languages',
            field=models.ManyToManyField(blank=True, related_name='language_spoken', to='users.languages'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_seen',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='linkedin_profile',
            field=models.CharField(blank=True, db_index=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mother_education',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mother_name',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mother_occupation',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mother_tongue',
            field=models.ManyToManyField(blank=True, related_name='mother_tongue', to='users.mothertongue'),
        ),
        migrations.AlterField(
            model_name='user',
            name='nature',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates your nature', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='notification_token',
            field=models.CharField(blank=True, db_index=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='own_car',
            field=models.CharField(blank=True, db_index=True, help_text='Candidate owns a car', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_age_from',
            field=models.PositiveIntegerField(db_index=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_age_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner age preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_age_to',
            field=models.PositiveIntegerField(db_index=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_caste_from',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_caste_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner caste preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_cities_from',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_cities_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner cities preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_country_from',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_country_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner country preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_expertise_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner expertise preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_graduation_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no graduation preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_height_from',
            field=models.PositiveIntegerField(db_index=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_height_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner height preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_height_to',
            field=models.PositiveIntegerField(db_index=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_income_from',
            field=models.PositiveIntegerField(db_index=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_income_to',
            field=models.PositiveIntegerField(db_index=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_marital_status_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner marital status preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_mothertongue_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner mother tongue preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_physicalstatus',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_postgraduation_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no postgrad preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_religion_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner religion preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_specialization_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no specialization preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_state_from',
            field=models.TextField(db_index=True, default='[]'),
        ),
        migrations.AlterField(
            model_name='user',
            name='partner_state_preference',
            field=models.BooleanField(db_index=True, default=False, help_text='If False then no partner state preference'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_is_verified',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='preferred_time_connect',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates preferred time for connect', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='profession_description',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='registration_number',
            field=models.CharField(blank=True, db_index=True, help_text="Indicates your doctor's registartion number", max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='religious_practices',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates religious practice of candidates', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='residence',
            field=models.CharField(blank=True, db_index=True, help_text='Indicates whether residence is owned or rented', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='schooling_details',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='sibling',
            field=models.IntegerField(blank=True, db_index=True, default=-1, help_text='Indicates whether user has siblings or not', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='time_birth',
            field=models.TimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='updated_date',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='work_out',
            field=models.IntegerField(blank=True, db_index=True, default=-1, help_text='If true you are a interested in yogs/gym/workout', null=True),
        ),
    ]
