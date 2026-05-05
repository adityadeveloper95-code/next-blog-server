from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_returns_ok_when_database_and_redis_are_up():
    client = APIClient()

    with patch("blog.services.health_service.connection.cursor") as mock_cursor, patch(
        "blog.services.health_service.get_redis_connection"
    ) as mock_get_redis_connection:
        cursor_cm = MagicMock()
        cursor = MagicMock()
        cursor_cm.__enter__.return_value = cursor
        mock_cursor.return_value = cursor_cm

        redis_client = MagicMock()
        mock_get_redis_connection.return_value = redis_client

        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "redis": "ok",
    }
    cursor.execute.assert_called_once_with("SELECT 1")
    redis_client.ping.assert_called_once()
