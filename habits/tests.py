from datetime import datetime, timedelta
from unittest.mock import patch

import pytz
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.test import APITestCase

from habits.models import Habit
from habits.services import send_information_about_new_habit_tg
from habits.tasks import telegram_message
from habits.validators import (validate_execution_time,
                               validate_linked_or_reward, validate_periodicity)

User = get_user_model()


class BaseHabitTestCase(APITestCase):
    """
    Базовый тестовый класс с методом setUp для создания пользователя и приятной привычки.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@user.com", password="testpass123"
        )
        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Home",
            time="08:00:00",
            action="Test pleasant habit",
            is_nice=True,
            duration=60,
            periodicity=1,
        )


class ValidatorsTestCase(BaseHabitTestCase):
    """
    Тесты для кастомных валидаторов привычек.
    """

    def test_linked_and_reward_conflict(self):
        """Нельзя указывать одновременно связанную привычку и награду."""
        data = {
            "reward": "Coffee",
            "related_habit": self.pleasant_habit.id,
            "is_nice": False,
        }
        with self.assertRaises(serializers.ValidationError) as context:
            validate_linked_or_reward(data)
        self.assertIn(
            "Нельзя одновременно указывать связанную привычку и вознаграждение.",
            str(context.exception),
        )

    def test_nice_habit_with_reward(self):
        """У приятной привычки не может быть награды."""
        data = {"is_nice": True, "reward": "Chocolate"}
        with self.assertRaises(serializers.ValidationError) as context:
            validate_linked_or_reward(data)
        self.assertIn(
            "У приятной привычки не может быть вознаграждения или связанной привычки.",
            str(context.exception),
        )

    def test_nice_habit_with_related(self):
        """У приятной привычки не может быть связанной привычки."""
        data = {"is_nice": True, "related_habit": self.pleasant_habit.id}
        with self.assertRaises(serializers.ValidationError) as context:
            validate_linked_or_reward(data)
        self.assertIn(
            "У приятной привычки не может быть вознаграждения или связанной привычки.",
            str(context.exception),
        )

    def test_execution_time_exceeds_limit(self):
        """Время выполнения не может превышать 120 секунд."""
        with self.assertRaises(serializers.ValidationError) as context:
            validate_execution_time(121)
        self.assertIn(
            "Время выполнения не может превышать 120 секунд.", str(context.exception)
        )

    def test_periodicity_too_low(self):
        """Периодичность не может быть меньше 1 дня."""
        with self.assertRaises(serializers.ValidationError) as context:
            validate_periodicity(0)
        self.assertIn(
            "Периодичность должна быть от 1 до 7 дней.", str(context.exception)
        )

    def test_periodicity_too_high(self):
        """Периодичность не может превышать 7 дней."""
        with self.assertRaises(serializers.ValidationError) as context:
            validate_periodicity(8)
        self.assertIn(
            "Периодичность должна быть от 1 до 7 дней.", str(context.exception)
        )


class HabitModelTestCase(BaseHabitTestCase):
    """
    Тесты для модели Habit и её метода clean.
    """

    def test_create_valid_habit(self):
        habit = Habit.objects.create(
            user=self.user,
            place="Office",
            time="09:00:00",
            action="Test action",
            duration=90,
            periodicity=2,
            reward="Coffee",
        )
        self.assertEqual(habit.action, "Test action")
        self.assertEqual(habit.periodicity, 2)

    def test_conflict_reward_and_related(self):
        habit = Habit(
            user=self.user,
            place="Park",
            time="10:00:00",
            action="Invalid",
            duration=100,
            reward="Conflict",
            related_habit=self.pleasant_habit,
        )
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_invalid_duration(self):
        habit = Habit(
            user=self.user,
            place="Gym",
            time="12:00:00",
            action="Too long",
            duration=150,
        )
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_nice_habit_with_reward_invalid(self):
        habit = Habit(
            user=self.user,
            place="Home",
            time="08:00:00",
            action="Invalid",
            is_nice=True,
            duration=60,
            reward="Invalid",
        )
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_periodicity_bounds(self):
        for value in [0, 8]:
            habit = Habit(
                user=self.user,
                place="Home",
                time="08:00:00",
                action="Invalid periodicity",
                duration=60,
                periodicity=value,
            )
            with self.assertRaises(ValidationError) as context:
                habit.full_clean()
            self.assertIn(
                "Периодичность должна быть от 1 до 7 дней", str(context.exception)
            )

        for value in [1, 7]:
            habit = Habit(
                user=self.user,
                place="Home",
                time="08:00:00",
                action="Valid periodicity",
                duration=60,
                periodicity=value,
            )
            try:
                habit.full_clean()
            except ValidationError:
                self.fail("Валидные значения вызвали ValidationError")

    def test_str_representation(self):
        habit = Habit.objects.create(
            user=self.user,
            place="Park",
            time="15:00:00",
            action="Evening walk",
            duration=30,
            periodicity=1,
        )
        self.assertEqual(str(habit), "Evening walk в 15:00:00 в Park")

        habit.time = "09:00:00"
        habit.place = "Office"
        habit.save()
        self.assertEqual(str(habit), "Evening walk в 09:00:00 в Office")


class TelegramServiceTestCase(APITestCase):
    """
    Тесты для сервиса отправки уведомлений в Telegram.
    """

    @patch("habits.services.requests.get")
    def test_send_successful_message(self, mock_get):
        mock_get.return_value.status_code = 200
        result = send_information_about_new_habit_tg("12345", "Test")
        self.assertTrue(result)
        mock_get.assert_called_once()

    @patch("habits.services.requests.get")
    def test_send_message_connection_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection failed")

        with self.assertRaises(requests.RequestException) as context:
            send_information_about_new_habit_tg("12345", "Test")

        self.assertIn(
            "Ошибка при отправке сообщения в Telegram", str(context.exception)
        )
        self.assertIsInstance(context.exception.__cause__, requests.RequestException)
        mock_get.assert_called_once()


class TelegramMessageTaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@gmail.com", password="testpass", telegram_id="123456789"
        )

        # Время привычки = сейчас + 5 минут (чтобы попало в окно 10 минут)
        zone = pytz.timezone(settings.CELERY_TIMEZONE)
        now = datetime.now(zone)
        habit_time = (now + timedelta(minutes=5)).time()

        self.habit = Habit.objects.create(
            user=self.user,
            place="Кухня",
            time=habit_time,
            action="Выпить воду",
            duration=60,
            periodicity=1,
        )

    @patch("habits.tasks.send_information_about_new_habit_tg")
    def test_telegram_message_sends_and_updates_time(self, mock_send):
        old_time = self.habit.time

        telegram_message()

        self.habit.refresh_from_db()

        # Проверка: сообщение было отправлено 1 раз
        mock_send.assert_called()
        self.assertGreaterEqual(mock_send.call_count, 1)

        # Проверка: время привычки обновилось (добавлен 1 день)
        zone = pytz.timezone(settings.CELERY_TIMEZONE)
        now = datetime.now(zone)
        expected_datetime = datetime.combine(now.date(), old_time) + timedelta(days=1)
        self.assertEqual(self.habit.time, expected_datetime.time())
