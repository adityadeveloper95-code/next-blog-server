from django.urls import path

from .views import (
    BlogByIdView,
    BlogDetailView,
    BlogView,
    CommentCreateView,
    CommentUpdateDeleteView,
    FeedView,
    HealthView,
    LoginView,
    LogoutView,
    UserView,
)


urlpatterns = [
    path(
        "health",
        HealthView.as_view(),
        name="health",
    ),
    path(
        "user",
        UserView.as_view(),
        name="user",
    ),
    path(
        "login",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "logout",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "feed",
        FeedView.as_view(),
        name="feed",
    ),
    path(
        "blog",
        BlogView.as_view(),
        name="blog",
    ),
    # Keep int route before slug route so numeric ids don't get captured by slug path.
    path(
        "blog/<int:pk>",
        BlogByIdView.as_view(),
        name="blog-update-delete",
    ),
    path(
        "blog/<slug:slug>",
        BlogDetailView.as_view(),
        name="blog-detail",
    ),
    path("blog/<int:blog_pk>/comment", CommentCreateView.as_view(), name="comment-create"),
    path(
        "blog/<int:blog_pk>/comment/<int:pk>",
        CommentUpdateDeleteView.as_view(),
        name="comment-update-delete",
    ),
]
