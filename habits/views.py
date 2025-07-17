from django.http import HttpResponse
from rest_framework import generics, permissions

from .models import Habit
from .paginators import HabitPagination
from .serializers import HabitSerializer
from .services import send_information_about_new_habit_tg


def home_view(request):
    return HttpResponse("""
    <h1>Добро пожаловать в Habits Tracker API!</h1>
    <p>Доступные эндпоинты:</p>
    <ul>
        <li><a href="/admin/">Админка</a></li>
        <li><a href="/swagger/">Swagger UI</a></li>
        <li><a href="/redoc/">ReDoc</a></li>
    </ul>
    """)


class HabitListCreateView(generics.ListCreateAPIView):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HabitPagination

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        habit = serializer.save(user=self.request.user)
        if habit.user.telegram_id:
            send_information_about_new_habit_tg(
                habit.user.telegram_id, "Создана новая привычка!"
            )


class HabitRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Habit.objects.filter(is_public=True).order_by("-id")
