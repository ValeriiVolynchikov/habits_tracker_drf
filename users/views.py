from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import CustomUser
from .serializers import UserSerializer


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)


class TokenRefreshCustomView(TokenRefreshView):
    permission_classes = (AllowAny,)
