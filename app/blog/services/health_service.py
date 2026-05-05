from django.db import connection
from django_redis import get_redis_connection


def check_health():
    database_status = "ok"
    redis_status = "ok"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database_status = "error"

    try:
        redis_client = get_redis_connection("default")
        redis_client.ping()
    except Exception:
        redis_status = "error"

    status = "ok" if database_status == "ok" and redis_status == "ok" else "unavailable"
    return {
        "status": status,
        "database": database_status,
        "redis": redis_status,
    }
