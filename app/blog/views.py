from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate, login, logout

from .serializers import (
    BlogCreateSerializer,
    BlogDetailSerializer,
    BlogUpdateSerializer,
    FeedOutputSerializer,
    BlogWriteOutputSerializer,
    CommentCreateSerializer,
    CommentOutputSerializer,
    CommentUpdateSerializer,
    LoginSerializer,
    UserCreateSerializer,
    UserOutputSerializer,
)
from .services import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    check_health,
    create_blog,
    create_comment,
    create_user,
    delete_comment,
    delete_blog,
    get_blog_by_slug,
    get_feed,
    update_comment,
    update_blog,
)


@api_view(["GET"])
def test_view(request):
    return Response({"message": "blog api is working"})


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        health = check_health()
        if health.get("status") == "ok":
            return Response(health, status=status.HTTP_200_OK)
        return Response(health, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            user = create_user(**serializer.validated_data)
        except ConflictError as exc:
            return Response(
                {"message": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            UserOutputSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserOutputSerializer(request.user).data, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        user = authenticate(request, **serializer.validated_data)
        if not user:
            return Response(
                {"message": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response(
            {"message": "Login successful.", "user": UserOutputSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class BlogCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BlogCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            blog = create_blog(user=request.user, **serializer.validated_data)
        except ConflictError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(
            BlogWriteOutputSerializer(blog).data,
            status=status.HTTP_201_CREATED,
        )


class BlogDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            blog = get_blog_by_slug(slug=slug)
        except NotFoundError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(BlogDetailSerializer(blog).data, status=status.HTTP_200_OK)


class FeedView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        page_raw = request.query_params.get("page", "1")
        try:
            page = int(page_raw)
        except (TypeError, ValueError):
            return Response(
                {"message": "Page must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page < 1:
            return Response(
                {"message": "Page must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = get_feed(page)
        return Response(FeedOutputSerializer(data).data, status=status.HTTP_200_OK)


class BlogUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        serializer = BlogUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            blog = update_blog(blog_id=pk, user=request.user, **serializer.validated_data)
        except NotFoundError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ForbiddenError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(BlogWriteOutputSerializer(blog).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            delete_blog(blog_id=pk, user=request.user)
        except NotFoundError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ForbiddenError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, blog_pk):
        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            comment = create_comment(blog_pk, request.user, serializer.validated_data["content"])
        except NotFoundError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(CommentOutputSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, blog_pk, pk):
        serializer = CommentUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            comment = update_comment(
                blog_pk,
                pk,
                request.user,
                serializer.validated_data["content"],
            )
        except NotFoundError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ForbiddenError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(CommentOutputSerializer(comment).data, status=status.HTTP_200_OK)

    def delete(self, request, blog_pk, pk):
        try:
            delete_comment(blog_pk, pk, request.user)
        except NotFoundError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ForbiddenError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_204_NO_CONTENT)
