from django.db import models
from rest_framework.authtoken.models import Token
from django.conf import settings

from django.contrib.auth.models import User
from django.dispatch import receiver

# # Create your models here.
# class Profile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
#     current_weight = models.FloatField(null=True, blank=True)  # Weight in kg
#     height = models.PositiveIntegerField(null=True, blank=True)  # Height in cm

#     bmi = models.FloatField(null=True, blank=True)  # Body Mass Index


#     age = models.PositiveIntegerField(null=True, blank=True)
#     weight = models.PositiveIntegerField(null=True, blank=True)  # Weight in kg
#     activity_level = models.CharField(
#         max_length=50,
#         choices=[
#             ('sedentary', 'Sedentary'),
#             ('lightly_active', 'Lightly Active'),
#             ('moderately_active', 'Moderately Active'),
#             ('very_active', 'Very Active'),
#         ],
#         null=True,
#         blank=True
#     )
#     goal = models.CharField(
#         max_length=50,
#         choices=[
#             ('weight_loss', 'Weight Loss'),
#             ('maintenance', 'Maintenance'),
#             ('weight_gain', 'Weight Gain'),
#             ('muscle_gain', 'Muscle Gain'),
#         ],
#         null=True,
#         blank=True
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = 'Profile'
#         verbose_name_plural = 'Profiles'
#         ordering = ['updated_at']



# your_app/models.py


# --- Your Existing Profile Model (Slightly Refined) ---
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    # Consolidated weight field
    current_weight = models.FloatField(null=True, blank=True, help_text="Weight in kilograms (kg)")
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Height in centimeters (cm)")
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], null=True, blank=True) # Added gender for better calorie calculation
    # storing main image text in the db
    image = models.TextField(blank=True, null=True, help_text="User's profile image.")
    activity_level = models.CharField(
        max_length=50,
        choices=[
            ('sedentary', 'Sedentary (little or no exercise)'),
            ('lightly_active', 'Lightly Active (light exercise/sports 1-3 days/week)'),
            ('moderately_active', 'Moderately Active (moderate exercise/sports 3-5 days/week)'),
            ('very_active', 'Very Active (hard exercise/sports 6-7 days a week)'),
        ],
        null=True, blank=True
    )
    goal = models.CharField(
        max_length=50,
        choices=[
            ('weight_loss', 'Weight Loss'),
            ('maintenance', 'Maintenance'),
            ('muscle_gain', 'Muscle Gain'),
        ],
        null=True, blank=True
    )
    # Optional: User can specify dietary preferences or restrictions
    dietary_preferences = models.TextField(blank=True, help_text="e.g., 'no red meat', 'prefers fish', 'allergic to groundnuts'")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # You can add a property for BMI if you like
    @property
    def bmi(self):
        if self.current_weight and self.height:
            return round(self.current_weight / ((self.height / 100) ** 2), 2)
        return None

    def __str__(self):
        return f"{self.user.username}'s Profile"

# --- New Models for Fitness Plans ---

class FitnessPlan(models.Model):
    """ The main container for a complete plan for a specific period. """
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='fitness_plans')
    start_date = models.DateField()
    end_date = models.DateField()
    goal_at_creation = models.CharField(null=True, blank=True, max_length=50, help_text="The user's goal when this plan was created.")
    is_active = models.BooleanField(default=True)

    # For debugging and fine-tuning your AI
    ai_prompt_text = models.TextField(blank=True, help_text="The exact prompt sent to the AI.")
    ai_response_raw = models.JSONField(blank=True, null=True, help_text="The raw JSON response from the AI.")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan for {self.profile.user.username} from {self.start_date} to {self.end_date}"


class WorkoutDay(models.Model):
    """ Represents a single day in a workout week. """
    plan = models.ForeignKey(FitnessPlan, on_delete=models.CASCADE, related_name='workout_days')
    DAY_CHOICES = [
        (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'),
        (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    title = models.CharField(max_length=100, help_text="e.g., 'Upper Body Strength' or 'Rest Day'")
    description = models.TextField(blank=True, help_text="General instructions for the day's workout.")
    is_rest_day = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['day_of_week']

class Exercise(models.Model):
    """ A specific exercise within a WorkoutDay. """
    workout_day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=100, help_text="e.g., 'Push-ups', 'Squats', 'Ampe (Jumping Game)'")
    sets = models.PositiveIntegerField()
    reps = models.CharField(max_length=50, help_text="e.g., '10-12', 'AMRAP (As Many Reps As Possible)'")
    rest_period_seconds = models.PositiveIntegerField(help_text="Rest time in seconds between sets.")
    notes = models.TextField(blank=True, help_text="Specific instructions or Ghanaian context.")

    def __str__(self):
        return f"{self.name} ({self.sets} sets of {self.reps})"


class NutritionDay(models.Model):
    """ Represents a single day's nutrition plan. """
    plan = models.ForeignKey(FitnessPlan, on_delete=models.CASCADE, related_name='nutrition_days')
    day_of_week = models.IntegerField(choices=WorkoutDay.DAY_CHOICES)
    notes = models.TextField(blank=True, help_text="General advice for the day, e.g., 'Drink 3L of water.'")
    
    # Target macronutrients for the day
    target_calories = models.PositiveIntegerField(null=True, blank=True)
    target_protein_grams = models.PositiveIntegerField(null=True, blank=True)
    target_carbs_grams = models.PositiveIntegerField(null=True, blank=True)
    target_fats_grams = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['day_of_week']

class Meal(models.Model):
    """ A specific meal within a NutritionDay, focused on Ghanaian cuisine. """
    nutrition_day = models.ForeignKey(NutritionDay, on_delete=models.CASCADE, related_name='meals')
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack')
    ]
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    description = models.CharField(max_length=255, help_text="e.g., 'Waakye with boiled egg and fish'")
    calories = models.PositiveIntegerField()
    protein_grams = models.FloatField()
    carbs_grams = models.FloatField()
    fats_grams = models.FloatField()
    portion_size = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., '1 medium ladle', '2 pieces of chicken'")
    
    def __str__(self):
        return f"{self.get_meal_type_display()}: {self.description}"


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)