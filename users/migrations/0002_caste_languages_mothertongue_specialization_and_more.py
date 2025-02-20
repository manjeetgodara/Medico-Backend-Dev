# Generated by Django 4.2.6 on 2023-11-29 05:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Caste',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Languages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='MotherTongue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Specialization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='beauty_consciousness',
            field=models.BooleanField(default=False, help_text='If true you are a conscious about beauty/body'),
        ),
        migrations.AddField(
            model_name='user',
            name='birth_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='blood_group',
            field=models.CharField(blank=True, help_text='Your Bloodgroup', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='body_build',
            field=models.CharField(blank=True, help_text='Indicates lean, wellbuild or heavy', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='body_clock',
            field=models.CharField(blank=True, help_text='Indicates whether you are a morning/latenight person', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='city_parents',
            field=models.CharField(blank=True, help_text='City where parents reside', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='complexion',
            field=models.CharField(blank=True, help_text='Indicates Complexion', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='country',
            field=models.CharField(blank=True, help_text='Country you live in', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='disease_history',
            field=models.CharField(blank=True, help_text='Disease/Surgery undergone', max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='facebook_profile',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='family_car',
            field=models.CharField(blank=True, help_text='Family owns a car', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='family_environment',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='family_financial_status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='family_house',
            field=models.CharField(blank=True, help_text='Whether house is owned or rented', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='father_education',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='father_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='father_occupation',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='foodie',
            field=models.BooleanField(default=False, help_text='If true you are a foodie'),
        ),
        migrations.AddField(
            model_name='user',
            name='graduation_institute',
            field=models.CharField(blank=True, max_length=356, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='graduation_status',
            field=models.CharField(blank=True, help_text='Your graduation status', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='horoscope_matching',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='instagram_profile',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='interest_music',
            field=models.CharField(blank=True, help_text='Indicates whether an art lover/music enthusiast', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='interest_party',
            field=models.CharField(blank=True, help_text='Indicates whether candidate loves dining or partying', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='kids_choice',
            field=models.CharField(blank=True, help_text='Indicates your preference on kids', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='linkedin_profile',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='mother_education',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='mother_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='mother_occupation',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='nature',
            field=models.CharField(blank=True, help_text='Indicates your nature', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='own_car',
            field=models.CharField(blank=True, help_text='Candidate owns a car', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_country_from',
            field=models.TextField(default='[]'),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_country_preference',
            field=models.BooleanField(default=False, help_text='If true then no partner country preference'),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_income_from',
            field=models.PositiveIntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_income_to',
            field=models.PositiveIntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_physicalstatus',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_specialization_preference',
            field=models.BooleanField(default=False, help_text='If true then no specialization preference'),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_state_from',
            field=models.TextField(default='[]'),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_state_preference',
            field=models.BooleanField(default=False, help_text='If true then no partner state preference'),
        ),
        migrations.AddField(
            model_name='user',
            name='physical_status',
            field=models.CharField(blank=True, help_text='Indicates normal or disabled', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='post_graduation_institute',
            field=models.CharField(blank=True, max_length=356, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='post_graduation_status',
            field=models.CharField(blank=True, help_text='Your graduation status', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='profession',
            field=models.TextField(default='[]'),
        ),
        migrations.AddField(
            model_name='user',
            name='profession_description',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='registration_number',
            field=models.CharField(blank=True, help_text="Indicates your doctor's registartion number", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='religious_practices',
            field=models.CharField(blank=True, help_text='Indicates religious practice of candidates', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='residence',
            field=models.CharField(blank=True, help_text='Indicates whether residence is owned or rented', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='schooling_details',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='sibling',
            field=models.BooleanField(default=False, help_text='Indicates whether user has siblings or not'),
        ),
        migrations.AddField(
            model_name='user',
            name='state',
            field=models.CharField(blank=True, help_text='State you live in', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='time_birth',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='work_out',
            field=models.BooleanField(default=False, help_text='If true you are a interested in yogs/gym/workout'),
        ),
        migrations.AlterField(
            model_name='partnerexpertisepreference',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partnerexpertisepreference', to='users.user'),
        ),
        migrations.AlterField(
            model_name='partnermaritalstatuspreference',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user'),
        ),
        migrations.AlterField(
            model_name='partnerreligionpreference',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user'),
        ),
        migrations.RemoveField(
            model_name='user',
            name='mother_tongue',
        ),
        migrations.AlterField(
            model_name='userpostgraduation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user'),
        ),
        migrations.CreateModel(
            name='SubCaste',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('caste', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='caste', to='users.caste')),
            ],
        ),
        migrations.CreateModel(
            name='Siblings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sibling_gender', models.CharField(blank=True, choices=[('m', 'Male'), ('f', 'Female')], max_length=10, null=True)),
                ('sibling_name', models.CharField(blank=True, max_length=100, null=True)),
                ('sibling_education', models.CharField(blank=True, max_length=100, null=True)),
                ('sibling_marital_status', models.CharField(blank=True, max_length=30, null=True)),
                ('sibling_profession', models.CharField(blank=True, max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_siblings', to='users.user')),
            ],
        ),
        migrations.CreateModel(
            name='PartnerSpecializationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specialization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.specialization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partnerspecializationpreference', to='users.user')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='languages',
            field=models.ManyToManyField(blank=True, related_name='language_spoken', to='users.languages'),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_mothertongue_from',
            field=models.ManyToManyField(blank=True, related_name='partner_mothertongue', to='users.mothertongue'),
        ),
        migrations.AddField(
            model_name='user',
            name='specialization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='specialization', to='users.specialization'),
        ),
        migrations.AddField(
            model_name='user',
            name='sub_caste',
            field=models.ForeignKey(blank=True, help_text='Your_subcaste', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_subcaste', to='users.subcaste'),
        ),
        migrations.AddField(
            model_name='user',
            name='mother_tongue',
            field=models.ManyToManyField(blank=True, related_name='mother_tongue', to='users.mothertongue'),
        ),
    ]
