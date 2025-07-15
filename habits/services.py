# habits/services.py
import requests
import logging
from django.conf import settings
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: int, message: str) -> bool:
    """
    Отправляет сообщение в Telegram
    :param chat_id: ID чата пользователя
    :param message: Текст сообщения
    :return: Статус отправки (True/False)
    """
    if not all([settings.TELEGRAM_BOT_TOKEN, chat_id, message]):
        logger.error("Не хватает данных для отправки в Telegram")
        return False

    url = f"{settings.TELEGRAM_URL}{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=5
        )
        response.raise_for_status()
        return True
    except RequestException as e:
        logger.error(f"Ошибка отправки в Telegram: {str(e)}")
        return False


def send_information_about_new_habit_tg(chat_id: int, habit) -> bool:
    """
    Отправляет уведомление о новой привычке
    :param chat_id: ID чата пользователя
    :param habit: Объект привычки
    :return: Статус отправки
    """
    if not habit:
        return False

    message = (
        f"🎯 *Новая привычка создана!*\n\n"
        f"*Действие:* {habit.action}\n"
        f"*Место:* {habit.place}\n"
        f"*Время:* {habit.time.strftime('%H:%M')}\n"
        f"*Периодичность:* {habit.get_frequency_display()}\n"
        f"*Награда:* {habit.reward or 'Нет'}"
    )

    return send_telegram_message(chat_id, message)
