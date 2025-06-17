from django.db import models
from rest_framework.authtoken.models import Token
from django.conf import settings

from django.contrib.auth.models import User
from django.dispatch import receiver

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    current_weight = models.FloatField(null=True, blank=True)  # Weight in kg
    height = models.PositiveIntegerField(null=True, blank=True)  # Height in cm

    bmi = models.FloatField(null=True, blank=True)  # Body Mass Index


    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.PositiveIntegerField(null=True, blank=True)  # Weight in kg
    activity_level = models.CharField(
        max_length=50,
        choices=[
            ('sedentary', 'Sedentary'),
            ('lightly_active', 'Lightly Active'),
            ('moderately_active', 'Moderately Active'),
            ('very_active', 'Very Active'),
        ],
        null=True,
        blank=True
    )
    goal = models.CharField(
        max_length=50,
        choices=[
            ('weight_loss', 'Weight Loss'),
            ('maintenance', 'Maintenance'),
            ('weight_gain', 'Weight Gain'),
            ('muscle_gain', 'Muscle Gain'),
        ],
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['updated_at']

@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)