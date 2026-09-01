from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "role"]

    def validate_role(self, value):
        if value not in [
            User.Role.ADMIN,
            User.Role.ENGINEER,
            User.Role.ANALYST,
            User.Role.DEVICE,
        ]:
            raise serializers.ValidationError("Invalid user role specified.")
        return value
