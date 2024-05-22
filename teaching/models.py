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


class LearnerQuizPerformance(models.Model):
    learner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    quiz_step = models.ForeignKey('courses.QuizLessonStep', on_delete=models.CASCADE)
    attempts = models.PositiveIntegerField(default=1)
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['learner', 'quiz_step']

    def __str__(self):
        return f'{self.learner} - {self.quiz_step} - {"Correct" if self.passed else "Incorrect"}'


class AssessmentAnalytics(models.Model):
    learner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)

    @property
    def quiz_performance(self):
        return LearnerQuizPerformance.objects.filter(
            learner=self.learner,
            quiz_step__lesson__chapter__course=self.course
        )

    @property
    def code_challenge_performance(self):
        return CodeChallengeSubmission.objects.filter(
            learner=self.learner,
            code_challenge_step__lesson__chapter__course=self.course
        )

    @property
    def quiz_success_rate(self):
        total_quizzes = self.quiz_performance.count()
        correct_quizzes = self.quiz_performance.filter(is_correct=True).count()
        return (correct_quizzes / total_quizzes) * 100 if total_quizzes > 0 else 0

    @property
    def code_challenge_success_rate(self):
        total_challenges = self.code_challenge_performance.count()
        successful_challenges = self.code_challenge_performance.filter(passed=True).count()
        return (successful_challenges / total_challenges) * 100 if total_challenges > 0 else 0

    @property
    def overall_success_rate(self):
        total_assessments = self.quiz_performance.count() + self.code_challenge_performance.count()
        successful_assessments = self.quiz_performance.filter(is_correct=True).count() + self.code_challenge_performance.filter(passed=True).count()
        return (successful_assessments / total_assessments) * 100 if total_assessments > 0 else 0

    @property
    def total_quiz_attempts(self):
        return sum(performance.attempts for performance in self.quiz_performance.all())

    @property
    def total_code_challenge_attempts(self):
        return sum(submission.attempts for submission in self.code_challenge_performance.all())

    def __str__(self):
        return f'{self.learner} - {self.course} - Overall Success Rate: {self.overall_success_rate:.2f}%'
