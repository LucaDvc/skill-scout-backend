from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(CourseEnrollment)
admin.site.register(CodeChallengeSubmission)
admin.site.register(TestResult)
admin.site.register(LearnerProgress)
