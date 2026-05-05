import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class ConflictError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


USERNAME_REGEX = re.compile(r"^[a-z0-9]{3,30}$")


def create_user(name, username, password):
    if not USERNAME_REGEX.fullmatch(username):
        raise ValidationError(
            {"username": "Username must be 3-30 chars using lowercase letters and digits only."}
        )

    if User.objects.filter(username=username).exists():
        raise ConflictError("Username is already taken.")

    return User.objects.create_user(
        username=username,
        password=password,
        first_name=name,
    )
