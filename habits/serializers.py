from rest_framework import serializers

from habits.models import Habit
from habits.validators import (
    validate_execution_time,
    validate_linked_or_reward,
    validate_periodicity,
)


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = ["user"]

    def validate(self, data):
        return validate_linked_or_reward(data)

    def validate_duration(self, value):
        return validate_execution_time(value)

    def validate_periodicity(self, value):
        return validate_periodicity(value)
