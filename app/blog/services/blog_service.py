from math import ceil

from django.db.models import Count

from ..models import Blog

from .exceptions import ConflictError, ForbiddenError, NotFoundError


def create_blog(user, title, slug, content):
    if Blog.objects.filter(slug=slug).exists():
        raise ConflictError("Slug is already taken.")

    return Blog.objects.create(
        user=user,
        title=title,
        slug=slug,
        content=content,
    )


def update_blog(blog_id, user, title, content):
    try:
        blog = Blog.objects.get(id=blog_id)
    except Blog.DoesNotExist as exc:
        raise NotFoundError("Blog not found.") from exc

    if blog.user_id != user.id:
        raise ForbiddenError("You do not have permission to edit this blog.")

    blog.title = title
    blog.content = content
    blog.save(update_fields=["title", "content", "updated_at"])
    return blog


def delete_blog(blog_id, user):
    try:
        blog = Blog.objects.get(id=blog_id)
    except Blog.DoesNotExist as exc:
        raise NotFoundError("Blog not found.") from exc

    if blog.user_id != user.id:
        raise ForbiddenError("You do not have permission to delete this blog.")

    blog.delete()


def get_blog_by_slug(slug):
    try:
        return Blog.objects.prefetch_related("comments__user").get(slug=slug)
    except Blog.DoesNotExist as exc:
        raise NotFoundError("Blog not found.") from exc


def get_feed(page, page_size=20):
    if page < 1:
        raise ValueError("Page must be greater than or equal to 1.")

    queryset = Blog.objects.annotate(comment_count=Count("comments")).order_by("-created_at")
    total_items = queryset.count()
    total_pages = ceil(total_items / page_size) if total_items else 0
    offset = (page - 1) * page_size
    items = list(queryset[offset : offset + page_size])

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "items": items,
    }
