from django.urls import path

from . import views

urlpatterns = [
    path("", views.onboarding, name="onboarding"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("progress/", views.progress, name="progress"),
    path("get_meal_list/", views.get_meal_list, name="get_meal_list"),
    path("get_daily_summary/", views.get_daily_summary, name="get_daily_summary"),
    path("add_food/", views.add_food, name="add_food"),
    path("delete_food/<int:food_id>/", views.delete_food, name="delete_food"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("health-check", views.health_check),
    # path("register/", views.register_user, name="register"),
]
