from ..models import Blog, Comment

from .exceptions import ForbiddenError, NotFoundError


def create_comment(blog_id, user, content):
    try:
        blog = Blog.objects.get(id=blog_id)
    except Blog.DoesNotExist as exc:
        raise NotFoundError("Blog not found.") from exc

    return Comment.objects.create(
        blog=blog,
        user=user,
        content=content,
    )


def update_comment(blog_id, comment_id, user, content):
    try:
        Blog.objects.get(id=blog_id)
    except Blog.DoesNotExist as exc:
        raise NotFoundError("Blog not found.") from exc

    try:
        comment = Comment.objects.get(id=comment_id, blog_id=blog_id)
    except Comment.DoesNotExist as exc:
        raise NotFoundError("Comment not found.") from exc

    if comment.user_id != user.id:
        raise ForbiddenError("You do not have permission to edit this comment.")

    comment.content = content
    comment.save(update_fields=["content", "updated_at"])
    return comment


def delete_comment(blog_id, comment_id, user):
    try:
        Blog.objects.get(id=blog_id)
    except Blog.DoesNotExist as exc:
        raise NotFoundError("Blog not found.") from exc

    try:
        comment = Comment.objects.get(id=comment_id, blog_id=blog_id)
    except Comment.DoesNotExist as exc:
        raise NotFoundError("Comment not found.") from exc

    if comment.user_id != user.id:
        raise ForbiddenError("You do not have permission to delete this comment.")

    comment.delete()
