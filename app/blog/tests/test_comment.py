import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from blog.models import Blog, Comment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_comment_returns_201_with_nested_author(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")
    api_client.force_authenticate(user=commenter)

    response = api_client.post(
        f"/api/blog/{blog.id}/comment",
        {"content": "Nice post"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["blog_id"] == blog.id
    assert body["content"] == "Nice post"
    assert body["author"]["id"] == commenter.id


@pytest.mark.django_db
def test_create_comment_returns_401_when_unauthenticated(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")

    response = api_client.post(
        f"/api/blog/{blog.id}/comment",
        {"content": "Nice post"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_comment_returns_404_when_blog_not_found(api_client):
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    api_client.force_authenticate(user=commenter)

    response = api_client.post(
        "/api/blog/99999/comment",
        {"content": "Nice post"},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_create_comment_returns_422_for_blank_content(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")
    api_client.force_authenticate(user=commenter)

    response = api_client.post(
        f"/api/blog/{blog.id}/comment",
        {"content": ""},
        format="json",
    )

    assert response.status_code == 422


@pytest.mark.django_db
def test_update_comment_returns_200(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")
    comment = Comment.objects.create(blog=blog, user=commenter, content="Old")
    api_client.force_authenticate(user=commenter)

    response = api_client.put(
        f"/api/blog/{blog.id}/comment/{comment.id}",
        {"content": "Updated"},
        format="json",
    )

    assert response.status_code == 200
    comment.refresh_from_db()
    assert comment.content == "Updated"


@pytest.mark.django_db
def test_update_comment_returns_403_for_non_owner(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    other = User.objects.create_user(username="other", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")
    comment = Comment.objects.create(blog=blog, user=commenter, content="Old")
    api_client.force_authenticate(user=other)

    response = api_client.put(
        f"/api/blog/{blog.id}/comment/{comment.id}",
        {"content": "Updated"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_update_comment_returns_404_when_comment_not_found(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")
    api_client.force_authenticate(user=commenter)

    response = api_client.put(
        f"/api/blog/{blog.id}/comment/99999",
        {"content": "Updated"},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_comment_returns_204(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")
    comment = Comment.objects.create(blog=blog, user=commenter, content="Old")
    api_client.force_authenticate(user=commenter)

    response = api_client.delete(f"/api/blog/{blog.id}/comment/{comment.id}")

    assert response.status_code == 204
    assert not Comment.objects.filter(id=comment.id).exists()


@pytest.mark.django_db
def test_delete_comment_returns_403_for_non_owner(api_client):
    author = User.objects.create_user(username="author", password="strongpass123")
    commenter = User.objects.create_user(username="commenter", password="strongpass123")
    other = User.objects.create_user(username="other", password="strongpass123")
    blog = Blog.objects.create(user=author, title="Post", slug="post", content="Content")
    comment = Comment.objects.create(blog=blog, user=commenter, content="Old")
    api_client.force_authenticate(user=other)

    response = api_client.delete(f"/api/blog/{blog.id}/comment/{comment.id}")

    assert response.status_code == 403
