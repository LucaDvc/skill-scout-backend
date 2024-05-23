from django.db import models

from courses.models import BaseLessonStep
from learning.models import CodeChallengeSubmission, LearnerProgress


class EngagementAnalytics(models.Model):
    learner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    lesson_step = models.ForeignKey('courses.BaseLessonStep', on_delete=models.CASCADE)
    time_spent = models.DurationField()  # Store the total time spent on a lesson step
    last_accessed = models.DateTimeField(auto_now=True)  # Track the last accessed time

    class Meta:
        unique_together = ['learner', 'lesson_step']

    def __str__(self):
        return f'{self.learner} - {self.lesson_step} - {self.time_spent}'


class DailyActiveUsersAnalytics(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    date = models.DateField()
    active_users = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('course', 'date')

    def __str__(self):
        return f'{self.course} - {self.date} - Active Users: {self.active_users}'


class CourseCompletionAnalytics(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    learners_completed = models.PositiveIntegerField(default=0)
    learners_in_progress = models.PositiveIntegerField(default=0)

    def update_completion_stats(self):
        total_learners = self.course.enrolled_learners.count()
        completed_learners = self.course.courseenrollment_set.filter(completed=True).count()
        in_progress_learners = total_learners - completed_learners

        self.learners_completed = completed_learners
        self.learners_in_progress = in_progress_learners
        self.save()

    @classmethod
    def identify_drop_off_points(cls, course):
        lesson_steps = BaseLessonStep.objects.filter(lesson__chapter__course=course)
        drop_off_points = {}

        for step in lesson_steps:
            # Count learners who have accessed this step
            learners_accessed = EngagementAnalytics.objects.filter(lesson_step=step).values(
                'learner').distinct().count()

            # Count learners who have this step as their last completed step
            learners_stopped = LearnerProgress.objects.filter(last_stopped_step=step).count()

            if learners_accessed > 0 and learners_stopped > 0:
                drop_off_rate = (learners_stopped / learners_accessed) * 100
                drop_off_points[step] = {
                    'learners_accessed': learners_accessed,
                    'learners_stopped': learners_stopped,
                    'drop_off_rate': drop_off_rate
                }

        return drop_off_points

    def __str__(self):
        return f'{self.course} - Completed: {self.learners_completed}, In Progress: {self.learners_in_progress}'
