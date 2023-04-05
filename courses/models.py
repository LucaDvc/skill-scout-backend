import datetime

from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator, FileExtensionValidator
from django.db import models
import uuid
from django.db.models import Avg


class Course(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    # instructors
    title = models.CharField(max_length=100, null=False, blank=False)
    intro = models.TextField(max_length=300, null=True, blank=True)  # change to False for production
    description = models.TextField(null=True, blank=True, validators=[
        MinLengthValidator(100, 'the description must be at least 100 characters long')
    ])  # change to True for production
    requirements = models.TextField(null=True, blank=True)  # change to False for production
    total_hours = models.DecimalField(max_digits=3, decimal_places=0, null=True, blank=True)  # change to False for production
    creation_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(default=0, max_digits=4, decimal_places=0, null=True,blank=True, validators=[
        MinValueValidator(0)
    ])
    image = models.ImageField(null=True, blank=True)  # add default
    tags = models.ManyToManyField('Tag', blank=True)

    @property
    def average_rating(self):
        return self.review_set.all().aggregate(Avg('rating'))['rating__avg']

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name='price_gte_0'),
        ]

    def __str__(self):
        return self.title


class Review(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    # learner =
    rating = models.IntegerField(null=False, blank=False, validators=[
        MinValueValidator(1),
        MaxValueValidator(5)
    ])
    comment = models.TextField(max_length=500, null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(rating__range=(1, 5)), name='rating_between_1_5'),
            models.UniqueConstraint(fields=['rating'], name='rating_once')  # add learner field to constraint later
        ]

    def __str__(self):
        return self.course.__str__() + ': ' + self.rating.__str__()


class Tag(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name


class Chapter(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.title


class TextLessonStep(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    text = models.TextField(null=True, blank=True)  # change to False for production
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)


class QuizLessonStep(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    question = models.TextField(max_length=500, null=False, blank=False)
    explanation = models.TextField(max_length=500, null=True, blank=True)  # change to False for production
    preserve_order = models.BooleanField(default=True)


class QuizChoice(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    quiz = models.ForeignKey(QuizLessonStep, on_delete=models.CASCADE)
    text = models.CharField(max_length=100, null=False, blank=False)
    correct = models.BooleanField(null=False, blank=False)

    def __str__(self):
        return self.text


class VideoLessonStep(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    video_file = models.FileField(null=True, blank=True, validators=[
        FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])
    ])  # change to False for production, add upload_to=...
