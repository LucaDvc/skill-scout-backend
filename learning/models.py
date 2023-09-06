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
