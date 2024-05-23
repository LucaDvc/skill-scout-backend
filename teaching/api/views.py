import json
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Count, Avg, Max
from django.http import Http404
from rest_framework import generics, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework import parsers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta

from courses import cache_utils
from learning.models import CourseEnrollment
from courses.api.serializers import CourseSerializer, ChapterSerializer, LessonSerializer
from courses.api.lesson_steps_serializers import TextLessonStepSerializer, \
    QuizLessonStepSerializer, QuizChoiceSerializer, VideoLessonStepSerializer, CodeChallengeLessonStepSerializer, \
    CodeChallengeTestCaseSerializer
from .serializers import CourseEnrollmentSerializer, DailyActiveUsersAnalyticsSerializer
from courses.models import Course, Chapter, Lesson, TextLessonStep, QuizLessonStep, QuizChoice, VideoLessonStep, \
    BaseLessonStep, CodeChallengeLessonStep, CodeChallengeTestCase
from ..analytics import CourseAssessmentAnalytics
from ..models import CourseCompletionAnalytics, DailyActiveUsersAnalytics, EngagementAnalytics


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['active']

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(instructor=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instructor = self.request.user
            serializer.save(instructor=instructor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(instructor=user)

    def get_object(self):
        course_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=course_id)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()

        # Parse tags if they are a string
        tags_data = request.data.get('tags')
        if isinstance(tags_data, str):
            try:
                tags_data = json.loads(tags_data)
            except json.JSONDecodeError:
                return Response({'detail': 'Invalid JSON format for tags'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(tags=tags_data, chapters=request.data.get('chapters'))
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChapterListCreateView(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id)
        return Chapter.objects.filter(course__instructor=self.request.user, course=course)

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs['course_id'], instructor=self.request.user)
        serializer.save(course=course)


class ChapterRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chapter.objects.filter(course__instructor=self.request.user)

    def get_object(self):
        chapter_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=chapter_id)


class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chapter_id = self.kwargs['chapter_id']
        return Lesson.objects.filter(chapter__course__instructor=self.request.user, chapter__id=chapter_id)

    def perform_create(self, serializer):
        if 'order' in self.request.data:
            raise serializers.ValidationError(
                {"order": "You cannot set the order value directly when creating a new lesson."})
        chapter = get_object_or_404(Chapter, id=self.kwargs['chapter_id'], course__instructor=self.request.user)
        last_lesson = Lesson.objects.filter(chapter=chapter).order_by('-order').first()
        highest_order = last_lesson.order if last_lesson else 0
        serializer.save(chapter=chapter, order=highest_order + 1)


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(chapter__course__instructor=self.request.user)

    def get_object(self):
        lesson_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=lesson_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lesson'] = self.get_object()  # Ensure 'lesson' is included in the context
        return context

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

    def validate_request_data(self, request):
        pass

    def get_lesson(self):
        return get_object_or_404(Lesson, id=self.kwargs['lesson_id'],
                                 chapter__course__instructor=self.request.user)

    def perform_create(self, serializer):
        self.validate_request_data(self.request)

        if 'order' in self.request.data:
            raise serializers.ValidationError(
                {"order": "You cannot set the order value directly when creating a new lesson step."})
        if 'type' in self.request.data:
            raise serializers.ValidationError(
                {"type": "You cannot set the type value for a lesson step."})
        lesson = self.get_lesson()
        last_lesson_step = len(lesson.baselessonstep_set.all())
        highest_order = last_lesson_step if last_lesson_step else 0
        base_lesson_step = BaseLessonStep.objects.create(lesson=lesson, order=highest_order + 1)
        serializer.save(base_step=base_lesson_step)


class BaseLessonStepRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), base_step__id=pk)

    def perform_update(self, serializer):
        lesson_step = self.get_object()
        base_lesson_step = lesson_step.base_step
        lesson = base_lesson_step.lesson
        order = base_lesson_step.order
        all_lesson_steps = lesson.baselessonstep_set.all()
        if self.request.data.get('order'):
            new_order = int(self.request.data.get('order'))
            if order == new_order or new_order is None:
                base_lesson_step.save()
                serializer.save()
                return
            elif new_order > len(all_lesson_steps):
                raise serializers.ValidationError(
                    {"order": "Order value cannot be bigger than the total number of lesson steps in the lesson"}
                )
            else:
                if new_order > order:
                    affected_lesson_steps = list(
                        filter(lambda x: order < x.order <= new_order, all_lesson_steps))
                    for step in affected_lesson_steps:
                        step.order = step.order - 1
                        step.save()
                    base_lesson_step.order = new_order
                else:
                    affected_lesson_steps = list(
                        filter(lambda x: new_order <= x.order < order, all_lesson_steps))
                    for step in affected_lesson_steps:
                        step.order = step.order + 1
                        step.save()
                    base_lesson_step.order = new_order

        base_lesson_step.save()
        serializer.save()


class TextLessonStepListCreateView(BaseLessonStepListCreateView):
    serializer_class = TextLessonStepSerializer

    def get_queryset(self):
        lesson = self.get_lesson()
        return TextLessonStep.objects.filter(base_step__lesson=lesson)


class TextLessonStepRetrieveUpdateDestroyView(BaseLessonStepRetrieveUpdateDestroyView):
    serializer_class = TextLessonStepSerializer

    def get_queryset(self):
        lessons = Lesson.objects.filter(chapter__course__instructor=self.request.user)
        return TextLessonStep.objects.filter(base_step__lesson__in=lessons)


class QuizLessonStepListCreateView(BaseLessonStepListCreateView):
    serializer_class = QuizLessonStepSerializer

    def get_queryset(self):
        lesson = self.get_lesson()
        return QuizLessonStep.objects.filter(base_step__lesson=lesson)


class QuizLessonStepRetrieveUpdateDestroyView(BaseLessonStepRetrieveUpdateDestroyView):
    serializer_class = QuizLessonStepSerializer

    def get_queryset(self):
        lessons = Lesson.objects.filter(chapter__course__instructor=self.request.user)
        return QuizLessonStep.objects.filter(base_step__lesson__in=lessons)


class QuizChoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizChoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_quiz_step(self):
        quiz_id = self.kwargs['quiz_id']
        try:
            quiz = QuizLessonStep.objects.get(base_step_id=quiz_id,
                                              base_step__lesson__chapter__course__instructor=self.request.user)
        except QuizLessonStep.DoesNotExist:
            raise Http404

        return quiz

    def get_queryset(self):
        quiz = self.get_quiz_step()
        return QuizChoice.objects.filter(quiz=quiz)

    def perform_create(self, serializer):
        quiz = self.get_quiz_step()
        serializer.save(quiz=quiz)


class QuizChoiceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuizChoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        quizzes = QuizLessonStep.objects.filter(base_step__lesson__chapter__course__instructor=self.request.user)
        return QuizChoice.objects.filter(quiz__in=quizzes)

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=pk)


class VideoLessonStepListCreateView(BaseLessonStepListCreateView):
    serializer_class = VideoLessonStepSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        lesson = get_object_or_404(Lesson, id=lesson_id, chapter__course__instructor=self.request.user)
        return VideoLessonStep.objects.filter(base_step__lesson=lesson)


class VideoLessonStepRetrieveUpdateDestroyView(BaseLessonStepRetrieveUpdateDestroyView):
    serializer_class = VideoLessonStepSerializer

    def get_queryset(self):
        lessons = Lesson.objects.filter(chapter__course__instructor=self.request.user)
        return VideoLessonStep.objects.filter(base_step__lesson__in=lessons)


class CodeChallengeLessonStepListCreateView(BaseLessonStepListCreateView):
    serializer_class = CodeChallengeLessonStepSerializer

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        lesson = get_object_or_404(Lesson, id=lesson_id, chapter__course__instructor=self.request.user)
        code_steps = CodeChallengeLessonStep.objects.filter(base_step__lesson=lesson)

        # get the languages from the cache or fallback to the db if necessary
        languages, from_cache = cache_utils.get_languages()

        # fetch related languages from cache
        if from_cache:
            languages_dict = {lang.id: lang for lang in languages}
            for step in code_steps:
                if step.language_id in languages_dict:
                    step.language = languages_dict[step.language_id]

        return code_steps

    def validate_request_data(self, request):
        language_id = request.data.get('language_id')
        try:
            language, _ = cache_utils.get_language_by_id(language_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({'error': 'Invalid language id'})


class CodeChallengeLessonStepRetrieveUpdateDestroyView(BaseLessonStepRetrieveUpdateDestroyView):
    serializer_class = CodeChallengeLessonStepSerializer

    def get_queryset(self):
        lessons = Lesson.objects.filter(chapter__course__instructor=self.request.user)
        return CodeChallengeLessonStep.objects.filter(base_step__lesson__in=lessons)

    def get_object(self):
        pk = self.kwargs['pk']
        code_step = get_object_or_404(self.get_queryset(), base_step__id=pk)

        # fetch related language from cache
        try:
            language, from_cache = cache_utils.get_language_by_id(code_step.language_id)
            code_step.language = language
        except ObjectDoesNotExist:
            return Response({'error': 'Invalid language id'}, status=status.HTTP_400_BAD_REQUEST)

        return code_step


class CodeChallengeTestCaseListCreateView(generics.ListCreateAPIView):
    serializer_class = CodeChallengeTestCaseSerializer
    permission_classes = [IsAuthenticated]

    def get_code_challenge(self):
        code_challenge_id = self.kwargs['code_challenge_id']
        return get_object_or_404(
            CodeChallengeLessonStep,
            base_step_id=code_challenge_id,
            base_step__lesson__chapter__course__instructor=self.request.user
        )

    def get_queryset(self):
        code_challenge = self.get_code_challenge()
        return CodeChallengeTestCase.objects.filter(code_challenge_step=code_challenge)

    def perform_create(self, serializer):
        code_challenge = self.get_code_challenge()
        serializer.save(code_challenge_step=code_challenge)


class CodeChallengeTestCaseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CodeChallengeTestCaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        code_challenges = CodeChallengeLessonStep.objects.filter(
            base_step__lesson__chapter__course__instructor=self.request.user)
        return CodeChallengeTestCase.objects.filter(code_challenge_step__in=code_challenges)

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=pk)


class CourseEnrolledLearnersListView(generics.ListAPIView):
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.filter(instructor=user)
        course_id = self.kwargs['course_id']
        course = get_object_or_404(courses, id=course_id)
        return CourseEnrollment.objects.filter(course=course)

# TODO: ENDPOINT TO PUBLISH COURSE, WITH VALIDATION OF THE USER PROFILE (CAN'T BE PRIVATE), OTHER VALIDATIONS


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_enrollment_analytics(request, course_id):
    instructor = request.user
    course = get_object_or_404(Course, id=course_id, instructor=instructor)

    enrollment_counts_by_date = (
        CourseEnrollment.objects
        .filter(course=course)
        .annotate(enrollment_date=TruncDate('enrolled_at'))
        .values('enrollment_date')
        .annotate(count=Count('id'))
        .order_by('enrollment_date')
    )

    enrollment_data = list(enrollment_counts_by_date)

    return Response(enrollment_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_completion_analytics(request, course_id):
    instructor = request.user
    course = get_object_or_404(Course, id=course_id, instructor=instructor)
    course_completion, created = CourseCompletionAnalytics.objects.get_or_create(course=course)
    course_completion.update_completion_stats()

    return Response({'learners_completed': course_completion.learners_completed,
                     'learners_in_progress': course_completion.learners_in_progress})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_daily_activity_analytics(request, course_id):
    instructor = request.user
    course = get_object_or_404(Course, id=course_id, instructor=instructor)

    # Get optional date range from query parameters
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        # Default start date to course release date or to one month ago
        start_date = course.release_date if course.release_date else datetime.now().date() - timedelta(days=30)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Default end date to today
        end_date = datetime.now().date()

    # Fetch analytics data for the given course and date range
    analytics_data = DailyActiveUsersAnalytics.objects.filter(
        course=course,
        date__range=[start_date, end_date]
    )

    serializer = DailyActiveUsersAnalyticsSerializer(analytics_data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_engagement_analytics(request, course_id):
    instructor = request.user
    course = get_object_or_404(Course, id=course_id, instructor=instructor)

    # Aggregate data
    engagement_data = EngagementAnalytics.objects.filter(course=course).values('lesson_step').annotate(
        average_time_spent=Avg('time_spent'),
        learners_count=Count('learner'),
        last_accessed=Max('last_accessed')
    )

    # Fetch all lesson steps in a single query and prefetch related lesson and chapter data
    lesson_steps = BaseLessonStep.objects.filter(
        id__in=[entry['lesson_step'] for entry in engagement_data]
    ).select_related('lesson__chapter')

    # Create a dictionary for quick lookup
    lesson_steps_dict = {str(step.id): step for step in lesson_steps}

    # Sort the lesson steps according to the course structure
    sorted_lesson_steps = sorted(
        lesson_steps,
        key=lambda step: (
            step.lesson.chapter.creation_date,
            step.lesson.order,
            step.order
        )
    )

    # Enrich data with lesson step details
    enriched_data = []
    for step in sorted_lesson_steps:
        entry = next(item for item in engagement_data if str(item['lesson_step']) == str(step.id))
        if hasattr(step, 'text_step'):
            lesson_step_type = 'text'
        elif hasattr(step, 'quiz_step'):
            lesson_step_type = 'quiz'
        elif hasattr(step, 'video_step'):
            lesson_step_type = 'video'
        elif hasattr(step, 'code_challenge_step'):
            lesson_step_type = 'codechallenge'
        else:
            lesson_step_type = 'unknown'
        enriched_data.append({
            'lesson_step_id': str(step.id),
            'lesson_step_order': step.order,
            'lesson_title': step.lesson.title,
            'lesson_step_type': lesson_step_type,
            'average_time_spent': entry['average_time_spent'],
            'learners_count': entry['learners_count'],
            'last_accessed': entry['last_accessed']
        })

    return Response(enriched_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_assessments_analytics(request, course_id):
    instructor = request.user
    course = get_object_or_404(Course, id=course_id, instructor=instructor)
    stats = CourseAssessmentAnalytics.get_course_statistics(course)
    return Response(stats)
