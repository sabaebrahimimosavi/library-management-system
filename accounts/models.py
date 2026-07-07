from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        MEMBER = "MEMBER", "Member"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.MEMBER
    )

    def __str__(self):
        return self.email
