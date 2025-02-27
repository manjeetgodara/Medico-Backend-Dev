# Generated by Django 4.2.6 on 2024-01-08 05:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_user_other_hobbies'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='nts_beauty_consciousness',
            field=models.BooleanField(default=False, help_text='if True then it means user does not want to say/talk about being beauty/body consciousness'),
        ),
        migrations.AddField(
            model_name='user',
            name='nts_foodie',
            field=models.BooleanField(default=False, help_text='if True then it means user does not want to say/talk about being foodie'),
        ),
        migrations.AddField(
            model_name='user',
            name='nts_manglik',
            field=models.BooleanField(default=False, help_text='if True then it means user does not want to say/talk about being manglik'),
        ),
        migrations.AddField(
            model_name='user',
            name='nts_sibling',
            field=models.BooleanField(default=False, help_text='if True then it means user does not want to say/talk about being sibling'),
        ),
        migrations.AddField(
            model_name='user',
            name='nts_work_out',
            field=models.BooleanField(default=False, help_text='if True then it means user does not want to say/talk about doing workout'),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_graduation_preference',
            field=models.BooleanField(default=False, help_text='If true then no graduation preference'),
        ),
        migrations.AddField(
            model_name='user',
            name='partner_postgraduation_preference',
            field=models.BooleanField(default=False, help_text='If true then no postgrad preference'),
        ),
        migrations.CreateModel(
            name='PartnerPGPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_graduation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.postgraduation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
        migrations.CreateModel(
            name='PartnerGraduationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('graduation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.graduation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
    ]
