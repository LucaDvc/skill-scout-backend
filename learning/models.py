import uuid

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models


class CourseEnrollment(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    learner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    completed = models.BooleanField(default=False)
    favourite = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['course', 'learner']

    def __str__(self):
        return f'{self.course}: {self.learner}'


class LearnerProgress(models.Model):
    learner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    last_stopped_chapter = models.ForeignKey('courses.Chapter', on_delete=models.SET_NULL, null=True, blank=True)
    last_stopped_lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    last_stopped_step = models.ForeignKey('courses.BaseLessonStep', on_delete=models.SET_NULL, null=True, blank=True)

    completed_chapters = ArrayField(models.UUIDField(), default=list, blank=True)
    completed_lessons = ArrayField(models.UUIDField(), default=list, blank=True)
    completed_steps = ArrayField(models.UUIDField(), default=list, blank=True)

    @property
    def completion_ratio(self):
        chapters = self.course.chapter_set.all()
        total_lessons_count = sum(chapter.lesson_set.count() for chapter in chapters)
        completed_lessons_count = len(self.completed_lessons)

        if total_lessons_count == 0:
            return 0

        return (completed_lessons_count / total_lessons_count) * 100

    class Meta:
        unique_together = ['learner', 'course']

    def __str__(self):
        return f'{self.course}: {self.learner} - progress'


class CodeChallengeSubmission(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    learner = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='code_challenge_submissions')
    code_challenge_step = models.ForeignKey('courses.CodeChallengeLessonStep', on_delete=models.CASCADE, related_name='submissions')
    submitted_code = models.TextField(null=True, blank=True)  # change to false
    error_message = models.TextField(null=True, blank=True)
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['learner', 'code_challenge_step']


class TestResult(models.Model):
    submission = models.ForeignKey('learning.CodeChallengeSubmission', models.CASCADE, related_name='test_results')
    test_case = models.ForeignKey('courses.CodeChallengeTestCase', models.CASCADE)
    status = models.CharField(max_length=55, null=True, blank=True)
    compile_err = models.TextField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)
    stdout = models.TextField(null=True, blank=True)
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['submission', 'test_case']


class LearnerAssessmentStepPerformance(models.Model):
    learner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    base_step = models.ForeignKey('courses.BaseLessonStep', on_delete=models.CASCADE)
    attempts = models.PositiveIntegerField(default=1)
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['learner', 'base_step']

    def __str__(self):
        return f'{self.learner} - {self.base_step} - {"Correct" if self.passed else "Incorrect"}'
