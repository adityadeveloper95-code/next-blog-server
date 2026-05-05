import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from blog.models import Blog, Comment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_blog_returns_201_with_nested_author(api_client):
    user = User.objects.create_user(username="owner", password="strongpass123", first_name="Owner")
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/api/blog",
        {"title": "My Post", "slug": "my-post", "content": "Post content"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "My Post"
    assert body["slug"] == "my-post"
    assert body["author"]["id"] == user.id
    assert body["author"]["name"] == "Owner"


@pytest.mark.django_db
def test_create_blog_returns_409_for_duplicate_slug(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    Blog.objects.create(user=owner, title="Existing", slug="dup-slug", content="content")
    api_client.force_authenticate(user=owner)

    response = api_client.post(
        "/api/blog",
        {"title": "New", "slug": "dup-slug", "content": "new content"},
        format="json",
    )

    assert response.status_code == 409


@pytest.mark.django_db
def test_create_blog_returns_401_when_unauthenticated(api_client):
    response = api_client.post(
        "/api/blog",
        {"title": "My Post", "slug": "my-post", "content": "Post content"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_blog_returns_422_for_blank_title_or_content(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    api_client.force_authenticate(user=owner)

    response_blank_title = api_client.post(
        "/api/blog",
        {"title": "", "slug": "my-post", "content": "Post content"},
        format="json",
    )
    response_blank_content = api_client.post(
        "/api/blog",
        {"title": "My Post", "slug": "my-post-2", "content": ""},
        format="json",
    )

    assert response_blank_title.status_code == 422
    assert response_blank_content.status_code == 422


@pytest.mark.django_db
def test_update_blog_returns_200_and_keeps_slug_unchanged(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    blog = Blog.objects.create(user=owner, title="Old", slug="my-post", content="Old content")
    api_client.force_authenticate(user=owner)

    response = api_client.put(
        f"/api/blog/{blog.id}",
        {"title": "Updated", "content": "Updated content"},
        format="json",
    )

    assert response.status_code == 200
    blog.refresh_from_db()
    assert blog.title == "Updated"
    assert blog.content == "Updated content"
    assert blog.slug == "my-post"


@pytest.mark.django_db
def test_update_blog_returns_403_for_non_owner(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    other = User.objects.create_user(username="other", password="strongpass123")
    blog = Blog.objects.create(user=owner, title="Old", slug="my-post", content="Old content")
    api_client.force_authenticate(user=other)

    response = api_client.put(
        f"/api/blog/{blog.id}",
        {"title": "Updated", "content": "Updated content"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_update_blog_returns_404_when_blog_not_found(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    api_client.force_authenticate(user=owner)

    response = api_client.put(
        "/api/blog/99999",
        {"title": "Updated", "content": "Updated content"},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_blog_returns_204_and_removes_blog(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    blog = Blog.objects.create(user=owner, title="Old", slug="my-post", content="Old content")
    api_client.force_authenticate(user=owner)

    response = api_client.delete(f"/api/blog/{blog.id}")

    assert response.status_code == 204
    assert not Blog.objects.filter(id=blog.id).exists()


@pytest.mark.django_db
def test_delete_blog_returns_403_for_non_owner(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    other = User.objects.create_user(username="other", password="strongpass123")
    blog = Blog.objects.create(user=owner, title="Old", slug="my-post", content="Old content")
    api_client.force_authenticate(user=other)

    response = api_client.delete(f"/api/blog/{blog.id}")

    assert response.status_code == 403


@pytest.mark.django_db
def test_delete_blog_returns_404_when_blog_not_found(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123")
    api_client.force_authenticate(user=owner)

    response = api_client.delete("/api/blog/99999")

    assert response.status_code == 404


@pytest.mark.django_db
def test_get_blog_by_slug_returns_blog_with_comments(api_client):
    owner = User.objects.create_user(username="owner", password="strongpass123", first_name="Owner")
    commenter = User.objects.create_user(
        username="commenter", password="strongpass123", first_name="Commenter"
    )
    blog = Blog.objects.create(user=owner, title="My Post", slug="my-post", content="Post content")
    comment = Comment.objects.create(blog=blog, user=commenter, content="Nice post")

    response = api_client.get(f"/api/blog/{blog.slug}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == blog.id
    assert body["slug"] == "my-post"
    assert len(body["comments"]) == 1
    assert body["comments"][0]["id"] == comment.id
    assert body["comments"][0]["author"]["id"] == commenter.id


@pytest.mark.django_db
def test_get_blog_by_slug_returns_404_when_not_found(api_client):
    response = api_client.get("/api/blog/does-not-exist")

    assert response.status_code == 404
