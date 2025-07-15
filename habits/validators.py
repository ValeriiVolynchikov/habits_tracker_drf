from rest_framework import serializers


def validate_linked_or_reward(data):
    if data.get("reward") and data.get("related_habit"):
        raise serializers.ValidationError(
            "Нельзя одновременно указывать связанную привычку и вознаграждение."
        )
    if data.get("is_nice") and (data.get("reward") or data.get("related_habit")):
        raise serializers.ValidationError(
            "У приятной привычки не может быть вознаграждения или связанной привычки."
        )
    return data


def validate_execution_time(value):
    if value > 120:
        raise serializers.ValidationError(
            "Время выполнения не может превышать 120 секунд."
        )
    return value


def validate_periodicity(value):
    if value < 1 or value > 7:
        raise serializers.ValidationError("Периодичность должна быть от 1 до 7 дней.")
    return value
