from django.contrib import admin

from main.models import UserProfile, FoodEntry

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(FoodEntry)
