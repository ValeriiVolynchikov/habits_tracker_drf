from rest_framework.test import APITestCase

from users.models import CustomUser


class UserModelTest(APITestCase):
    def test_user_creation_success(self):
        """Тест успешного создания пользователя"""
        email = "testuser@example.com"
        password = "testpass123"

        user = CustomUser.objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(
            user.check_password(password)
        )  # Проверяем, что пароль установлен корректно
        self.assertTrue(user.is_active)  # По умолчанию пользователь активен
        self.assertFalse(user.is_staff)  # Не персонал
        self.assertFalse(user.is_superuser)  # Не суперпользователь
        self.assertEqual(str(user), email)  # Проверяем строковое представление
