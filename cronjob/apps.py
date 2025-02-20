# MLP/cronjob/apps.py

from django.apps import AppConfig

class CronjobConfig(AppConfig):
    name = 'cronjob'
    path = '/home/ubuntu/Medico-Backend/cronjob'  # Adjust the path as per your actual filesystem location
