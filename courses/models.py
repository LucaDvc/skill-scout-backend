from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator, FileExtensionValidator
from django.db import models
import uuid
from django.db.models import Avg
from learning.models import CourseEnrollment
from users.models import User


class Course(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=False, blank=False)
    category = models.ForeignKey('courses.Category', on_delete=models.SET_NULL, null=True, blank=True)
    intro = models.TextField(max_length=300, null=True, blank=True)
    description = models.TextField(null=True, blank=True, validators=[
        MinLengthValidator(100, 'the description must be at least 100 characters long')
    ])  # change to False for production

    class DifficultyLevel(models.TextChoices):
        OPTION_ONE = '1', 'Beginner'
        OPTION_TWO = '2', 'Intermediate'
        OPTION_THREE = '3', 'Advanced'

    level = models.CharField(max_length=50, null=True, blank=True,
                             choices=DifficultyLevel.choices)  # change to False for production

    requirements = models.TextField(null=True, blank=True)  # change to False for production
    total_hours = models.DecimalField(max_digits=3, decimal_places=0, null=True,
                                      blank=True)  # change to False for production
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    release_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(default=0, max_digits=4, decimal_places=0, null=True, blank=True, validators=[
        MinValueValidator(0)
    ])
    image = models.ImageField(null=True, blank=True, upload_to='courses/images/', default='courses/images/default.jpg')
    tags = models.ManyToManyField('Tag', blank=True)
    active = models.BooleanField(default=False, null=False, blank=False)
    enrolled_learners = models.ManyToManyField(User, through=CourseEnrollment, related_name='courses_enrolled')

    @property
    def average_rating(self):
        return self.review_set.all().aggregate(Avg('rating'))['rating__avg']

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name='price_gte_0'),
        ]

    def __str__(self):
        return self.title


class Category(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    supercategory = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True,
                                      related_name='subcategories')
    top = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    learner = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(null=False, blank=False, validators=[
        MinValueValidator(1),
        MaxValueValidator(5)
    ])
    comment = models.TextField(max_length=500, null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)  # change to last edited

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(rating__range=(1, 5)), name='rating_between_1_5'),
            models.UniqueConstraint(fields=['course', 'learner'], name='unique_review_per_learner_per_course')
        ]

    def __str__(self):
        return f'{self.course}, {self.learner} : {self.rating} stars'


class Tag(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True,
                          editable=False)  # change to models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name


class Chapter(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=False, blank=False)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['creation_date']


class Lesson(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, null=False, blank=False)
    order = models.PositiveIntegerField(null=False, blank=True)

    class Meta:
        ordering = ['order']

    def recalculate_order_values(self, chapter=None):
        if chapter is None:
            chapter = self.chapter
        remaining_lessons = chapter.lesson_set.all().order_by('order')
        for index, lesson in enumerate(remaining_lessons, start=1):
            if lesson.order != index:
                lesson.order = index
                lesson.save()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.recalculate_order_values()

    def __str__(self):
        return self.title


class BaseLessonStep(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(editable=True, blank=True)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if (hasattr(self, 'text_step') + hasattr(self, 'quiz_step')
                + hasattr(self, 'video_step') + hasattr(self, 'code_challenge_step')
                + hasattr(self, 'sorting_problem_step') + hasattr(self, 'text_problem_step') > 1):
            raise ValidationError('A BaseLessonStep can only have one type of child step.')
        super().save(*args, **kwargs)

    def recalculate_order_values(self):
        remaining_steps = self.lesson.baselessonstep_set.all()
        for index, step in enumerate(remaining_steps, start=1):
            if index != step.order:
                step.order = index
                step.save()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.recalculate_order_values()


class TextLessonStep(models.Model):
    base_step = models.OneToOneField(BaseLessonStep, on_delete=models.CASCADE, primary_key=True,
                                     related_name='text_step')
    text = models.TextField(null=True, blank=True)  # change to False for production


class QuizLessonStep(models.Model):
    base_step = models.OneToOneField(BaseLessonStep, on_delete=models.CASCADE, primary_key=True,
                                     related_name='quiz_step')
    question = models.TextField(max_length=500, null=False, blank=False)
    explanation = models.TextField(max_length=500, null=True, blank=True)  # change to False for production


class QuizChoice(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    quiz = models.ForeignKey(QuizLessonStep, to_field='base_step', on_delete=models.CASCADE)
    text = models.CharField(max_length=100, null=False, blank=False)
    correct = models.BooleanField(null=False, blank=False, default=False)

    def __str__(self):
        return self.text


class VideoLessonStep(models.Model):
    base_step = models.OneToOneField(BaseLessonStep, on_delete=models.CASCADE, primary_key=True,
                                     related_name='video_step')
    title = models.CharField(max_length=150, null=True, blank=True)  # change to False
    video_file = models.FileField(null=True, blank=True, validators=[
        FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])
    ], upload_to='courses/videos/')  # change to False for production, add upload_to=...


class CodeChallengeLessonStep(models.Model):
    base_step = models.OneToOneField(BaseLessonStep, on_delete=models.CASCADE, primary_key=True,
                                     related_name='code_challenge_step')
    title = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)  # change to False for prod
    initial_code = models.TextField(null=True, blank=True)  # change to False for prod
    language = models.ForeignKey('courses.ProgrammingLanguage', on_delete=models.SET_NULL, null=True)
    proposed_solution = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title


class ProgrammingLanguage(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f'{self.id}: {self.name}'


class CodeChallengeTestCase(models.Model):
    id = models.AutoField(primary_key=True, unique=True, editable=False)
    code_challenge_step = models.ForeignKey(CodeChallengeLessonStep, to_field='base_step', on_delete=models.CASCADE,
                                            related_name='test_cases')
    input = models.TextField(null=False, blank=False)
    expected_output = models.TextField(null=False, blank=False)

    class Meta:
        ordering = ['id']
        unique_together = ['code_challenge_step', 'input']


class SortingProblemLessonStep(models.Model):
    base_step = models.OneToOneField(BaseLessonStep, on_delete=models.CASCADE, primary_key=True,
                                     related_name='sorting_problem_step')
    title = models.CharField(max_length=100, null=False, blank=False)
    statement = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.title


class SortingProblemOption(models.Model):
    id = models.AutoField(primary_key=True, unique=True, editable=False)
    sorting_problem = models.ForeignKey(SortingProblemLessonStep, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=100, null=False, blank=False)
    correct_order = models.PositiveIntegerField(null=False, blank=False)

    class Meta:
        ordering = ['correct_order']

    def __str__(self):
        return self.text


class TextProblemLessonStep(models.Model):
    base_step = models.OneToOneField(BaseLessonStep, on_delete=models.CASCADE, primary_key=True,
                                     related_name='text_problem_step')
    title = models.CharField(max_length=100, null=False, blank=False)
    statement = models.TextField(null=False, blank=False)
    correct_answer = models.TextField(null=False, blank=False)
    case_sensitive = models.BooleanField(default=False, null=False, blank=False)
    allow_regex = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.title
