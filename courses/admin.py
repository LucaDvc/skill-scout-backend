from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Course)
admin.site.register(Category)
admin.site.register(Review)
admin.site.register(Tag)
admin.site.register(Chapter)
admin.site.register(Lesson)
admin.site.register(SortingProblemLessonStep)
admin.site.register(TextProblemLessonStep)
admin.site.register(TextLessonStep)
admin.site.register(QuizChoice)
admin.site.register(QuizLessonStep)
admin.site.register(VideoLessonStep)
admin.site.register(CodeChallengeLessonStep)
admin.site.register(CodeChallengeTestCase)
admin.site.register(ProgrammingLanguage)
