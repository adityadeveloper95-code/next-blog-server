import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from blog.models import Blog, Comment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seeded_feed_data():
    author = User.objects.create_user(username="author", password="strongpass123", first_name="Author")
    blogs = [
        Blog.objects.create(user=author, title="First", slug="first", content="One"),
        Blog.objects.create(user=author, title="Second", slug="second", content="Two"),
        Blog.objects.create(user=author, title="Third", slug="third", content="Three"),
    ]
    Comment.objects.create(blog=blogs[0], user=author, content="c1")
    Comment.objects.create(blog=blogs[0], user=author, content="c2")
    Comment.objects.create(blog=blogs[1], user=author, content="c3")
    return blogs


@pytest.mark.django_db
def test_feed_returns_200_with_paginated_shape(api_client, seeded_feed_data):
    response = api_client.get("/api/feed")

    assert response.status_code == 200
    body = response.json()
    assert set(["page", "page_size", "total_items", "total_pages", "items"]).issubset(body.keys())
    assert isinstance(body["items"], list)


@pytest.mark.django_db
def test_feed_page_1_has_accurate_total_items_and_total_pages(api_client, seeded_feed_data):
    response = api_client.get("/api/feed?page=1")

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 3
    assert body["total_pages"] == 1


@pytest.mark.django_db
def test_feed_page_99_returns_empty_items(api_client, seeded_feed_data):
    response = api_client.get("/api/feed?page=99")

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []


@pytest.mark.django_db
def test_feed_page_0_returns_400(api_client):
    response = api_client.get("/api/feed?page=0")

    assert response.status_code == 400


@pytest.mark.django_db
def test_feed_non_integer_page_returns_400(api_client):
    response = api_client.get("/api/feed?page=abc")

    assert response.status_code == 400


@pytest.mark.django_db
def test_feed_items_include_comment_count(api_client, seeded_feed_data):
    response = api_client.get("/api/feed?page=1")

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 3
    first = next(item for item in body["items"] if item["slug"] == "first")
    second = next(item for item in body["items"] if item["slug"] == "second")
    third = next(item for item in body["items"] if item["slug"] == "third")
    assert first["comment_count"] == 2
    assert second["comment_count"] == 1
    assert third["comment_count"] == 0
