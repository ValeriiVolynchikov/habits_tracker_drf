from django.urls import path

from .apps import UsersConfig
from .views import LoginView, TokenRefreshCustomView, UserCreateAPIView

app_name = UsersConfig.name

urlpatterns = [
    path("register/", UserCreateAPIView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshCustomView.as_view(), name="token_refresh"),
]
