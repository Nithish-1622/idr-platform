import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@idr.local",
        password="AdminPassword123!",
        role="ADMIN",
    )


@pytest.fixture
def engineer_user(db):
    user = User.objects.create_user(
        username="engineer",
        email="engineer@idr.local",
        password="EngineerPassword123!",
        role="ENGINEER",
    )
    return user


@pytest.fixture
def analyst_user(db):
    user = User.objects.create_user(
        username="analyst",
        email="analyst@idr.local",
        password="AnalystPassword123!",
        role="ANALYST",
    )
    return user


@pytest.fixture
def auth_client(api_client, engineer_user):
    api_client.force_authenticate(user=engineer_user)
    return api_client
