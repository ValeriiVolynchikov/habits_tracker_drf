from django.core.exceptions import ValidationError
from django.db import models

from config import settings


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="habits"
    )
    place = models.CharField(max_length=255, verbose_name="Место")
    time = models.TimeField(verbose_name="Время")
    action = models.CharField(max_length=255, verbose_name="Действие")
    is_nice = models.BooleanField(default=False, verbose_name="Приятная привычка")
    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_nice": True},
        related_name="related_to",
    )
    periodicity = models.PositiveIntegerField(
        default=1, verbose_name="Периодичность (дни)"
    )
    reward = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Вознаграждение"
    )
    duration = models.PositiveIntegerField(verbose_name="Время выполнения в секундах")
    is_public = models.BooleanField(default=False, verbose_name="Публичная привычка")

    def clean(self):
        if self.reward and self.related_habit:
            raise ValidationError(
                "Нельзя указывать одновременно вознаграждение и связанную привычку."
            )

        if self.duration > 120:
            raise ValidationError(
                "Время выполнения не должно превышать больше 120 секунд"
            )

        if self.is_nice and (self.reward or self.related_habit):
            raise ValidationError(
                "У приятной привычки не может быть вознаграждения или связанной привычки."
            )

        if self.periodicity < 1 or self.periodicity > 7:
            raise ValidationError("Периодичность должна быть от 1 до 7 дней")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.action} в {self.time} в {self.place}"

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
