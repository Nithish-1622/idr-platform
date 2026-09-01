import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_register_user_success(api_client):
    url = reverse("accounts:register")
    payload = {
        "username": "newdev",
        "email": "dev@idr.local",
        "password": "SecurePassword123!",
        "role": "ENGINEER",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["username"] == "newdev"
    assert response.data["role"] == "ENGINEER"
    assert "tokens" in response.data


@pytest.mark.django_db
def test_obtain_jwt_token(api_client, engineer_user):
    url = reverse("accounts:token_obtain_pair")
    payload = {"username": "engineer", "password": "EngineerPassword123!"}
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_current_user_profile(auth_client, engineer_user):
    url = reverse("accounts:current_user")
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == engineer_user.username
