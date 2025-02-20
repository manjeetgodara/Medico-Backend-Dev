from django.db import models

# Create your models here.


class ChangeLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    )

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    app_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    fields = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_action_display()} - {self.app_name} - {self.model_name}'
