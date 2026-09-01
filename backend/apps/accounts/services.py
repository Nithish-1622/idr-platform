from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def register_user_service(validated_data: dict) -> User:
    """Service function to create user with hashed password."""
    password = validated_data.pop("password")
    user = User(**validated_data)
    user.set_password(password)
    user.save()
    return user


def generate_tokens_for_user(user: User) -> dict[str, str]:
    """Generates SimpleJWT access and refresh tokens for user."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
