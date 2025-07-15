from django.urls import path

from .apps import HabitsConfig
from .views import (
    HabitListCreateView,
    HabitRetrieveUpdateDestroyView,
    PublicHabitListView,
)

app_name = HabitsConfig.name

urlpatterns = [
    path("public/", PublicHabitListView.as_view(), name="public-habit-list"),
    path("", HabitListCreateView.as_view(), name="habit-list-create"),
    path("<int:pk>/", HabitRetrieveUpdateDestroyView.as_view(), name="habit-detail"),
]
