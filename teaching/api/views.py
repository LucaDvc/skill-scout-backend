from django.db.models import F
from rest_framework import generics, status, serializers
from rest_framework.generics import get_object_or_404
from rest_framework import parsers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from learning.models import CourseEnrollment
from users.models import Instructor
from .serializers import CourseSerializer, ChapterSerializer, LessonSerializer, TextLessonStepSerializer, \
    QuizLessonStepSerializer, QuizChoiceSerializer, VideoLessonStepSerializer, CourseEnrollmentSerializer
from courses.models import Course, Chapter, Lesson, TextLessonStep, QuizLessonStep, QuizChoice, VideoLessonStep


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(instructor__user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instructor = Instructor.objects.get(user=self.request.user)
            serializer.save(instructor=instructor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(instructor__user=user)

    def get_object(self):
        course_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=course_id)


class ChapterListCreateView(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Chapter.objects.filter(course__instructor__user=self.request.user, course__id=course_id)

    def perform_create(self, serializer):
        course = Course.objects.get(id=self.kwargs['course_id'], instructor__user=self.request.user)
        serializer.save(course=course)


class ChapterRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chapter.objects.filter(course__instructor__user=self.request.user)

    def get_object(self):
        chapter_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=chapter_id)


class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chapter_id = self.kwargs['chapter_id']
        return Lesson.objects.filter(chapter__course__instructor__user=self.request.user, chapter__id=chapter_id)

    def perform_create(self, serializer):
        if 'order' in self.request.data:
            raise serializers.ValidationError(
                {"order": "You cannot set the order value directly when creating a new lesson."})
        chapter = Chapter.objects.get(id=self.kwargs['chapter_id'], course__instructor__user=self.request.user)
        last_lesson = Lesson.objects.filter(chapter=chapter).order_by('-order').first()
        highest_order = last_lesson.order if last_lesson else 0
        serializer.save(chapter=chapter, order=highest_order + 1)


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(chapter__course__instructor__user=self.request.user)

    def get_object(self):
        lesson_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=lesson_id)

    def perform_update(self, serializer):
        lesson = self.get_object()
        chapter = lesson.chapter
        order = lesson.order
        # check if the lesson is assigned to another chapter
        chapter_id = self.request.data.get('chapter_id')
        if chapter_id and chapter_id != str(chapter.id):
            other_chapter = Chapter.objects.get(id=chapter_id)
            if self.request.data.get('order'):
                order = int(self.request.data.get('order'))
                lesson_set = other_chapter.lesson_set
                lesson_count = lesson_set.count()
                if order > lesson_count and order != lesson_count:
                    order = lesson_count + 1
                else:
                    affected_lessons = lesson_set.filter(order__gte=order)
                    affected_lessons.update(order=F('order') + 1)
            else:
                order = other_chapter.lesson_set.count() + 1
            serializer.save(chapter=other_chapter, order=order)
            lesson.recalculate_order_values(chapter)
            return
        else:
            if self.request.data.get('order'):
                new_order = int(self.request.data.get('order'))
                if new_order == order:
                    serializer.save(chapter=chapter, order=order)
                    return
                elif new_order > chapter.lesson_set.count():
                    raise serializers.ValidationError(
                        {"order": "Order value cannot be bigger than the total number of lessons in the chapter"}
                    )
                else:
                    if new_order > order:
                        affected_lessons = chapter.lesson_set.filter(order__gt=order, order__lte=new_order)
                        affected_lessons.update(order=F('order') - 1)
                        order = new_order
                    else:
                        affected_lessons = chapter.lesson_set.filter(order__gte=new_order, order__lt=order)
                        affected_lessons.update(order=F('order') + 1)
                        order = new_order

        serializer.save(chapter=chapter, order=order)


class BaseLessonStepListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if 'order' in self.request.data:
            raise serializers.ValidationError(
                {"order": "You cannot set the order value directly when creating a new lesson step."})
        if 'type' in self.request.data:
            raise serializers.ValidationError(
                {"type": "You cannot set the type value for a lesson step."})
        lesson = Lesson.objects.get(id=self.kwargs['lesson_id'], chapter__course__instructor__user=self.request.user)
        last_lesson_step = len(lesson.get_lesson_steps())
        highest_order = last_lesson_step if last_lesson_step else 0
        serializer.save(lesson=lesson, order=highest_order + 1)


class BaseLessonStepRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=pk)

    def perform_update(self, serializer):
        lesson_step = self.get_object()
        lesson = lesson_step.lesson
        order = lesson_step.order
        if self.request.data.get('order'):
            new_order = int(self.request.data.get('order'))
            if order == new_order or new_order is None:
                serializer.save(lesson=lesson, order=order)
                return
            elif new_order > len(lesson.get_lesson_steps()):
                raise serializers.ValidationError(
                        {"order": "Order value cannot be bigger than the total number of lesson steps in the lesson"}
                    )
            else:
                lesson_steps = lesson.get_lesson_steps()
                if new_order > order:
                    affected_lesson_steps = list(
                        filter(lambda x: order < x.order <= new_order, lesson_steps))
                    for step in affected_lesson_steps:
                        step.order = step.order - 1
                        step.save()
                    order = new_order
                else:
                    affected_lesson_steps = list(
                        filter(lambda x: new_order <= x.order < order, lesson_steps))
                    for step in affected_lesson_steps:
                        step.order = step.order + 1
                        step.save()
                    order = new_order

        serializer.save(lesson=lesson, order=order)


class TextLessonStepListCreateView(BaseLessonStepListCreateView):
    serializer_class = TextLessonStepSerializer

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        lesson = Lesson.objects.get(id=lesson_id, chapter__course__instructor__user=self.request.user)
        return TextLessonStep.objects.filter(lesson=lesson)


class TextLessonStepRetrieveUpdateDestroyView(BaseLessonStepRetrieveUpdateDestroyView):
    serializer_class = TextLessonStepSerializer

    def get_queryset(self):
        lessons = Lesson.objects.filter(chapter__course__instructor__user=self.request.user)
        return TextLessonStep.objects.filter(lesson__in=lessons)


class QuizLessonStepListCreateView(BaseLessonStepListCreateView):
    serializer_class = QuizLessonStepSerializer

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        lesson = Lesson.objects.get(id=lesson_id, chapter__course__instructor__user=self.request.user)
        return QuizLessonStep.objects.filter(lesson=lesson)


class QuizLessonStepRetrieveUpdateDestroyView(BaseLessonStepRetrieveUpdateDestroyView):
    serializer_class = QuizLessonStepSerializer

    def get_queryset(self):
        lessons = Lesson.objects.filter(chapter__course__instructor__user=self.request.user)
        return QuizLessonStep.objects.filter(lesson__in=lessons)


class QuizChoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizChoiceSerializer

    def get_queryset(self):
        quiz_id = self.kwargs['quiz_id']
        quiz = QuizLessonStep.objects.get(id=quiz_id, lesson__chapter__course__instructor__user=self.request.user)
        return QuizChoice.objects.filter(quiz=quiz)

    def perform_create(self, serializer):
        quiz_id = self.kwargs['quiz_id']
        quiz = QuizLessonStep.objects.get(id=quiz_id, lesson__chapter__course__instructor__user=self.request.user)
        serializer.save(quiz=quiz)


class QuizChoiceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuizChoiceSerializer

    def get_queryset(self):
        quizzes = QuizLessonStep.objects.filter(lesson__chapter__course__instructor__user=self.request.user)
        return QuizChoice.objects.filter(quiz__in=quizzes)

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=pk)

    def perform_update(self, serializer):
        quiz_choice = self.get_object()
        quiz = quiz_choice.quiz
        serializer.save(quiz=quiz)


class VideoLessonStepListCreateView(BaseLessonStepListCreateView):
    serializer_class = VideoLessonStepSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        lesson = Lesson.objects.get(id=lesson_id, chapter__course__instructor__user=self.request.user)
        return VideoLessonStep.objects.filter(lesson=lesson)


class VideoLessonStepRetrieveUpdateDestroyView(BaseLessonStepRetrieveUpdateDestroyView):
    serializer_class = VideoLessonStepSerializer

    def get_queryset(self):
        lessons = Lesson.objects.filter(chapter__course__instructor__user=self.request.user)
        return VideoLessonStep.objects.filter(lesson__in=lessons)


class CourseEnrolledLearnersView(generics.ListAPIView):
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.filter(instructor__user=user)
        course_id = self.kwargs['course_id']
        course = get_object_or_404(courses, id=course_id)
        return CourseEnrollment.objects.filter(course=course)
