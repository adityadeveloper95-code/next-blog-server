import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_create_user_returns_201_with_expected_shape():
    client = APIClient()

    response = client.post(
        "/api/user",
        {
            "name": "Alice",
            "username": "alice123",
            "password": "strongpass123",
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert set(["id", "name", "username", "created_at", "updated_at"]).issubset(body.keys())
    assert body["name"] == "Alice"
    assert body["username"] == "alice123"
    assert User.objects.filter(username="alice123").exists()


@pytest.mark.django_db
def test_create_user_returns_409_for_duplicate_username():
    User.objects.create_user(username="alice123", password="strongpass123", first_name="Alice")
    client = APIClient()

    response = client.post(
        "/api/user",
        {
            "name": "Another Alice",
            "username": "alice123",
            "password": "anotherpass123",
        },
        format="json",
    )

    assert response.status_code == 409


@pytest.mark.django_db
def test_create_user_returns_422_for_invalid_username_chars():
    client = APIClient()

    response = client.post(
        "/api/user",
        {
            "name": "Alice",
            "username": "Alice@123",
            "password": "strongpass123",
        },
        format="json",
    )

    assert response.status_code == 422


@pytest.mark.django_db
def test_create_user_returns_422_for_short_password():
    client = APIClient()

    response = client.post(
        "/api/user",
        {
            "name": "Alice",
            "username": "alice123",
            "password": "short",
        },
        format="json",
    )

    assert response.status_code == 422


@pytest.mark.django_db
def test_create_user_returns_422_for_missing_required_fields():
    client = APIClient()

    response = client.post("/api/user", {"username": "alice123"}, format="json")

    assert response.status_code == 422


@pytest.mark.django_db
def test_login_returns_200_and_sets_session_cookie_with_valid_credentials():
    User.objects.create_user(username="alice123", password="strongpass123", first_name="Alice")
    client = APIClient()

    response = client.post(
        "/api/login",
        {"username": "alice123", "password": "strongpass123"},
        format="json",
    )

    assert response.status_code == 200
    assert "sessionid" in response.cookies


@pytest.mark.django_db
def test_login_returns_401_for_wrong_password():
    User.objects.create_user(username="alice123", password="strongpass123", first_name="Alice")
    client = APIClient()

    response = client.post(
        "/api/login",
        {"username": "alice123", "password": "wrongpass123"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_returns_200_when_logged_in():
    user = User.objects.create_user(username="alice123", password="strongpass123", first_name="Alice")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post("/api/logout", {}, format="json")

    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_returns_401_when_unauthenticated():
    client = APIClient()

    response = client.post("/api/logout", {}, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_get_user_returns_200_when_authenticated():
    user = User.objects.create_user(username="alice123", password="strongpass123", first_name="Alice")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/user")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["name"] == "Alice"
    assert body["username"] == "alice123"


@pytest.mark.django_db
def test_get_user_returns_401_when_unauthenticated():
    client = APIClient()

    response = client.get("/api/user")

    assert response.status_code == 401
