from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    GOAL_CHOICES = [
        ("lose", "Lose Weight"),
        ("gain", "Gain Weight"),
        ("maintain", "Maintain Weight"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_weight = models.FloatField(null=True, blank=True)
    target_weight = models.FloatField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    daily_calorie_goal = models.IntegerField(
        null=True, blank=True,
    )  # Simple fallback if user doesn't set
    goal_type = models.CharField(
        max_length=10, choices=GOAL_CHOICES, default="maintain"
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"


class FoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    grams = models.FloatField()
    calories = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.grams}g"
