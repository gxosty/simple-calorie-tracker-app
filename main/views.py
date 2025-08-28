from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.http import HttpResponse
from django.db import transaction

from .models import UserProfile, FoodEntry


# A simple BMR calculation function to use for calorie goal
def calculate_calorie_goal(goal_type):
    # This is a highly simplified calculation
    # For the brief, you can assume a standard baseline
    # 2000 cal for maintain, 1500 for lose, 2500 for gain
    if goal_type == "lose":
        return 1500
    elif goal_type == "gain":
        return 2500
    else:
        return 2000


def onboarding(request):
    if request.user.is_authenticated and request.user.is_active:
        return redirect("dashboard")

    step = request.session.get("onboarding_step", 1)
    form = None

    if request.method == "POST":
        if step == 1:
            # Step 1: Goal Type
            goal_type = request.POST.get("goal_type")
            if goal_type in [choice[0] for choice in UserProfile.GOAL_CHOICES]:
                request.session["onboarding_goal_type"] = goal_type
                request.session["onboarding_step"] = 2
                return redirect("onboarding")

        elif step == 2:
            # Step 2: Weight and Target
            current_weight = request.POST.get("current_weight")
            target_weight = request.POST.get("target_weight")

            request.session["onboarding_current_weight"] = float(current_weight)
            request.session["onboarding_target_weight"] = float(target_weight)
            request.session["onboarding_step"] = 3

            return redirect("onboarding")
        elif step == 3:
            # Step 3: User Account Creation
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)

                # Create a blank profile
                profile = UserProfile.objects.create(user=user)

                try:
                    # Use a transaction for safety
                    with transaction.atomic():
                        # profile = request.user.userprofile
                        profile.current_weight = request.session.get(
                            "onboarding_current_weight"
                        )
                        profile.target_weight = request.session.get(
                            "onboarding_target_weight"
                        )
                        profile.goal_type = request.session.get("onboarding_goal_type")

                        # Calculate and set calorie goal
                        profile.daily_calorie_goal = calculate_calorie_goal(
                            profile.goal_type
                        )

                        profile.save()
                except (ValueError, TypeError) as ex:
                    print("Try Except error: ", ex)
                    # Handle invalid input
                    pass  # Fall through to display the form again

                # Move to next step
                del request.session["onboarding_step"]
                del request.session["onboarding_current_weight"]
                del request.session["onboarding_target_weight"]
                del request.session["onboarding_goal_type"]
                # Onboarding complete, redirect to dashboard
                return redirect("dashboard")
            else:
                print("User creation error")

    context = {"step": step, "form": form, "goal_choices": UserProfile.GOAL_CHOICES}

    if step == 3:
        context["form"] = form or UserCreationForm()

    return render(request, "onboarding.html", context)


@login_required
def dashboard(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    today_entries = FoodEntry.objects.filter(
        user=request.user, timestamp__date=timezone.datetime.now().date()
    ).order_by("-timestamp")

    calories_consumed_today = sum(
        entry.calories for entry in today_entries if entry.calories is not None
    )

    context = {
        "profile": user_profile,
        "today_entries": today_entries,
        "calories_consumed_today": calories_consumed_today,
    }
    return render(request, "dashboard.html", context)


@login_required
def progress(request):
    user = request.user
    profile = user.userprofile

    all_entries = FoodEntry.objects.filter(user=user).order_by("timestamp")

    # Aggregate data by date
    daily_calories = {}
    for entry in all_entries:
        entry_date = entry.timestamp.date()
        if entry_date not in daily_calories:
            daily_calories[entry_date] = 0
        if entry.calories:
            daily_calories[entry_date] += entry.calories

    # Prepare date for chart.js
    # NOTE: For the weight chart, since we haven't implemented
    # a way for users to log their weight over time, we can show
    # a static representation with their starting weight and target
    # weight. In a real-world app, we would have a WeightLog model.
    sorted_daily_calories = sorted(daily_calories.keys())
    calorie_data = {
        "dates": [d.isoformat() for d in sorted_daily_calories],
        "calories": [daily_calories[d] for d in sorted_daily_calories],
    }

    context = {
        "profile": profile,
        "calorie_data_json": calorie_data,
    }

    return render(request, "progress.html", context)


def login_user(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard")
    else:
        form = AuthenticationForm()

    context = {"form": form}
    return render(request, "login.html", context)


@login_required
def logout_user(request):
    logout(request)
    return redirect("login")


@login_required
def get_meal_list(request):
    today_entries = FoodEntry.objects.filter(
        user=request.user, timestamp__date=timezone.datetime.now().date()
    ).order_by("-timestamp")

    return render(request, "partials/meal_list.html", {"today_entries": today_entries})


@login_required
def get_daily_summary(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    today_entries = FoodEntry.objects.filter(
        user=request.user, timestamp__date=timezone.datetime.now().date()
    ).order_by("-timestamp")

    calories_consumed_today = sum(
        entry.calories for entry in today_entries if entry.calories is not None
    )

    context = {
        "profile": user_profile,
        "today_entries": today_entries,
        "calories_consumed_today": calories_consumed_today,
    }
    return render(request, "partials/daily_summary.html", context)


@login_required
def add_food(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    name = request.POST.get("name")
    grams = request.POST.get("grams")
    calories = request.POST.get("calories")

    if not all([name, grams]):
        return HttpResponse("Food name and grams are required.", status=400)

    try:
        grams = float(grams)
        calories = float(calories) if calories else None
    except (ValueError, TypeError):
        return HttpResponse("Invalid input for grams or calories.", status=400)

    FoodEntry.objects.create(
        user=request.user, name=name, grams=grams, calories=calories
    )

    return HttpResponse(status=200, headers={"HX-Trigger": "meal-list-updated"})


@login_required
@csrf_exempt
def delete_food(request, food_id):
    if request.method == "POST":
        food_entry = get_object_or_404(FoodEntry, id=food_id, user=request.user)
        food_entry.delete()
        return HttpResponse(status=200, headers={"HX-Trigger": "meal-list-updated"})
    return HttpResponse(status=405)  # Method Not Allowed
