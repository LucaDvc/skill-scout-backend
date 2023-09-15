from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models


class CourseEnrollment(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    learner = models.ForeignKey('users.Learner', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    completed = models.BooleanField(default=False)
    favourite = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['course', 'learner']]

    def __str__(self):
        return f'{self.course}: {self.learner}'


class LearnerProgress(models.Model):
    learner = models.ForeignKey('users.Learner', on_delete=models.CASCADE)
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
