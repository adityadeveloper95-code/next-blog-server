from rest_framework import serializers


class UserCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100)
    username = serializers.RegexField(
        regex=r"^[a-z0-9]+$",
        min_length=3,
        max_length=30,
    )
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)


class UserOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source="first_name", read_only=True)
    username = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)
    updated_at = serializers.DateTimeField(
        source="last_login",
        read_only=True,
        allow_null=True,
    )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=30)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source="first_name", read_only=True)
    username = serializers.CharField(read_only=True)


class BlogCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=1, max_length=200)
    slug = serializers.SlugField(min_length=1, max_length=220)
    content = serializers.CharField(min_length=1, max_length=20000)


class BlogUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=1, max_length=200)
    content = serializers.CharField(min_length=1, max_length=20000)


class BlogWriteOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    author = AuthorSerializer(source="user", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=2000)


class CommentUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=2000)


class CommentOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    blog_id = serializers.IntegerField(read_only=True)
    content = serializers.CharField(read_only=True)
    author = AuthorSerializer(source="user", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class BlogDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    author = AuthorSerializer(source="user", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    comments = CommentOutputSerializer(many=True, read_only=True)


class FeedItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    author = AuthorSerializer(source="user", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class FeedOutputSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1)
    page_size = serializers.IntegerField(min_value=1)
    total_items = serializers.IntegerField(min_value=0)
    total_pages = serializers.IntegerField(min_value=0)
    items = FeedItemSerializer(many=True)
