from django.urls import path
from django.http import HttpResponseNotAllowed

from .views import (
    BlogCreateView,
    BlogDetailView,
    BlogUpdateDeleteView,
    CommentCreateView,
    CommentUpdateDeleteView,
    FeedView,
    HealthView,
    LoginView,
    LogoutView,
    UserCreateView,
    UserDetailView,
)


def map_methods(method_to_view):
    """Dispatch a URL to different APIViews by HTTP method."""
    prepared = {method.upper(): view.as_view() for method, view in method_to_view.items()}

    def routed_view(request, *args, **kwargs):
        view = prepared.get(request.method.upper())
        if view is None:
            return HttpResponseNotAllowed(list(prepared.keys()))
        return view(request, *args, **kwargs)

    return routed_view


urlpatterns = [
    path(
        "health",
        map_methods({"GET": HealthView}),
        name="health",
    ),
    path(
        "user",
        map_methods({"POST": UserCreateView, "GET": UserDetailView}),
        name="user",
    ),
    path(
        "login",
        map_methods({"POST": LoginView}),
        name="login",
    ),
    path(
        "logout",
        map_methods({"POST": LogoutView}),
        name="logout",
    ),
    path(
        "feed",
        map_methods({"GET": FeedView}),
        name="feed",
    ),
    path(
        "blog",
        map_methods({"POST": BlogCreateView}),
        name="blog",
    ),
    # Keep int route before slug route so numeric ids don't get captured by slug path.
    path(
        "blog/<int:pk>",
        map_methods({"PUT": BlogUpdateDeleteView, "DELETE": BlogUpdateDeleteView}),
        name="blog-update-delete",
    ),
    path(
        "blog/<slug:slug>",
        map_methods({"GET": BlogDetailView}),
        name="blog-detail",
    ),
    path("blog/<int:blog_pk>/comment", CommentCreateView.as_view(), name="comment-create"),
    path(
        "blog/<int:blog_pk>/comment/<int:pk>",
        CommentUpdateDeleteView.as_view(),
        name="comment-update-delete",
    ),
]
