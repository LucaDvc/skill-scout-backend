from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid

from learning.models import CourseEnrollment


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, first_name, last_name, **extra_fields):
        if not email:
            raise ValueError('Email must be provided')
        if not password:
            raise ValueError('Password must be provided')
        if not first_name:
            raise ValueError('First name must be provided')
        if not last_name:
            raise ValueError('Last name must be provided')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password, first_name, last_name, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, first_name, last_name, **extra_fields)

    def create_superuser(self, email, password, first_name, last_name, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, first_name, last_name, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # AbstractBaseUser has password, last_login and is_active by default
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    email = models.EmailField(db_index=True, unique=True, max_length=255, null=False, blank=False, error_messages={
            "unique": "A user with that email already exists.",
        })
    email_confirmed = models.BooleanField(default=False)
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, null=False, blank=False)
    city = models.CharField(max_length=255, null=True, blank=True)
    short_bio = models.CharField(max_length=255, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False, null=False, blank=False)
    picture = models.ImageField(null=True, blank=True,
                                upload_to='profiles/images/', default='profiles/images/user-default.png')
    linked_in = models.CharField(max_length=200, null=True, blank=True)
    facebook = models.CharField(max_length=200, null=True, blank=True)
    personal_website = models.CharField(max_length=200, null=True, blank=True)
    youtube = models.CharField(max_length=200, null=True, blank=True)
    enrolled_courses = models.ManyToManyField('courses.Course', through=CourseEnrollment,
                                              related_name='learners_enrolled')
    wishlist = models.ManyToManyField('courses.Course', related_name='wishlisted_by', blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
