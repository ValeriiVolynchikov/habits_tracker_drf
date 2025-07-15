from datetime import datetime, timedelta

import pytz
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from habits.models import Habit
from habits.services import send_information_about_new_habit_tg


@shared_task()
def telegram_message():
    timezone.activate(pytz.timezone(settings.CELERY_TIMEZONE))
    zone = pytz.timezone(settings.CELERY_TIMEZONE)
    now_time = datetime.now(zone)

    habits = Habit.objects.all()

    for habit in habits:
        user_tg = habit.user.telegram_id

        # Собираем datetime из даты сегодня и времени из habit.time
        habit_datetime = datetime.combine(now_time.date(), habit.time)
        habit_datetime = zone.localize(habit_datetime)

        if (
            user_tg
            and now_time >= habit_datetime - timedelta(minutes=10)
            and now_time <= habit_datetime + timedelta(minutes=10)
        ):
            message = f"Напоминание: {habit.action} в {habit.time.strftime('%H:%M')} {habit.place}"
            send_information_about_new_habit_tg(user_tg, message)

            if habit.reward:
                send_information_about_new_habit_tg(
                    user_tg, f"Поздравляю! Ты получил: {habit.reward}"
                )

            # Следующий день сдвигается по periodicity
            next_datetime = habit_datetime + timedelta(days=habit.periodicity)
            habit.time = next_datetime.time()
            habit.save()
