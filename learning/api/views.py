import re
from datetime import timedelta
from uuid import UUID

from celery.result import AsyncResult
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView

from courses.api.lesson_steps_serializers import QuizLessonStepSerializer, SortingProblemLessonStepSerializer, \
    TextProblemLessonStepSerializer, CodeChallengeLessonStepSerializer
from courses.api.serializers import ReviewSerializer
from learning.models import LearnerAssessmentStepPerformance, CodeChallengeSubmission
from teaching.models import EngagementAnalytics
from .mixins import LearnerCourseViewMixin
from .serializers import LearnerCourseSerializer, LearnerProgressSerializer
from courses.models import Course, CodeChallengeLessonStep, BaseLessonStep, QuizLessonStep, Review, \
    SortingProblemLessonStep, TextProblemLessonStep
from rest_framework.permissions import IsAuthenticated

from learning.models import LearnerProgress, CourseEnrollment
from learning.tasks import evaluate_code
from celery import states
from django.core.cache import cache


class LearnerCourseListView(generics.ListAPIView, LearnerCourseViewMixin):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = self.request.user
        enrolled_courses = Course.objects.filter(enrolled_learners=user)
        serialized_courses = []
        for course in enrolled_courses:
            course_data = self.get_course_data(course)
            serialized_courses.append(course_data)

        return Response(serialized_courses)


class LearnerCourseView(generics.RetrieveAPIView, LearnerCourseViewMixin):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners=user)

    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        course = self.get_object()
        enrolled_courses = Course.objects.filter(enrolled_learners=user)

        if course not in enrolled_courses:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        course_data = self.get_course_data(course)

        return Response(course_data)


class CodeChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user

        code = request.data.get('code')
        if not code or not code.strip():
            return Response({'error': 'code string cannot be blank'}, status=status.HTTP_400_BAD_REQUEST)

        acting_role = request.data.get('acting_role')
        if not acting_role:
            return Response({'error': 'acting_role is required'}, status=status.HTTP_400_BAD_REQUEST)
        if acting_role not in ['instructor', 'learner']:
            return Response({'error': 'invalid acting role'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            code_challenge_step = CodeChallengeLessonStep.objects.prefetch_related('test_cases')

            if acting_role == 'instructor':
                # Check if the user is the instructor for the course associated with this code challenge
                code_challenge_step = code_challenge_step.get(
                    base_step_id=pk,
                    base_step__lesson__chapter__course__instructor=user
                )
            else:
                # Check if the user is enrolled in the course associated with this code challenge
                code_challenge_step = code_challenge_step.get(
                    base_step_id=pk,
                    base_step__lesson__chapter__course__enrolled_learners=user
                )

        except CodeChallengeLessonStep.DoesNotExist:
            # Code challenge step does not exist or the user does not have the required role
            return Response({'detail': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        code_challenge_id = code_challenge_step.base_step_id
        cache.set(f'code_challenge_{code_challenge_id}', code_challenge_step, timeout=300)
        is_instructor = (acting_role == 'instructor')
        task = evaluate_code.delay(code, code_challenge_id, user.id, is_instructor)

        return Response({"token": str(task.id)})

    def get(self, request, pk):
        user = request.user

        try:
            code_challenge_step = CodeChallengeLessonStep.objects.prefetch_related('test_cases').get(
                base_step_id=pk,
                base_step__lesson__chapter__course__enrolled_learners=user
            )
        except CodeChallengeLessonStep.DoesNotExist:
            return Response({'detail': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        code_challenge_data = CodeChallengeLessonStepSerializer(code_challenge_step).data

        code_challenge_step_submission = CodeChallengeSubmission.objects.filter(learner=user,
                                                                                code_challenge_step=code_challenge_step).first()
        if code_challenge_step_submission:
            code_challenge_data['submitted_code'] = code_challenge_step_submission.submitted_code

        return Response(code_challenge_data)


class CodeChallengeResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        user = request.user
        enrolled = CodeChallengeLessonStep.objects.filter(
            base_step__lesson__chapter__course__enrolled_learners=user
        ).exists()
        if not enrolled:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        # check if the task is done and return the result
        result = AsyncResult(task_id)

        if result.ready():
            if result.status == states.SUCCESS:
                code_submission = result.result
                response_data = {
                    'task_status': states.SUCCESS,
                    'submission': code_submission
                }
                return Response(response_data)
            elif result.status == states.FAILURE:
                exception_message = str(result.result) if result.result else "Unknown Error"
                response_data = {
                    'task_status': states.FAILURE,
                    'error': exception_message
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': states.PENDING})


class QuizStepView(APIView):
    permission_classes = [IsAuthenticated]

    def get_quiz_step(self, pk, user):
        try:
            quiz_step = QuizLessonStep.objects.prefetch_related('quizchoice_set').get(
                base_step_id=pk,
                base_step__lesson__chapter__course__enrolled_learners=user
            )
        except QuizLessonStep.DoesNotExist:
            raise NotFound('Quiz not found')

        return quiz_step

    def get(self, request, pk):
        user = request.user

        quiz_step = self.get_quiz_step(pk, user)
        course_id = quiz_step.base_step.lesson.chapter.course_id

        learner_progress = LearnerProgress.objects.filter(learner=user, course_id=course_id).first()
        if not (learner_progress and quiz_step.base_step_id in learner_progress.completed_steps):
            quiz_data = QuizLessonStepSerializer(quiz_step, context={'is_learner': True}).data
        else:
            quiz_data = QuizLessonStepSerializer(quiz_step).data

        return Response(quiz_data)

    def post(self, request, pk):
        user = request.user

        quiz_step = self.get_quiz_step(pk, user)

        answer_ids = request.data.get('quiz_choices')
        if not isinstance(answer_ids, list) or not answer_ids:
            return Response({'error': 'quiz_choices must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure all elements UUIDs
        try:
            submitted_choices = set(UUID(choice_id) for choice_id in answer_ids)
        except (ValueError, AttributeError):
            return Response({'error': 'All quiz_choices must be valid UUID strings'},
                            status=status.HTTP_400_BAD_REQUEST)

        quiz_choices = quiz_step.quizchoice_set.all()

        # Set of all valid choice UUIDs for this quiz
        valid_choice_ids = {str(choice.id) for choice in quiz_choices}
        if not all(choice_id in valid_choice_ids for choice_id in answer_ids):
            return Response({'error': 'One or more quiz_choices are invalid'}, status=status.HTTP_400_BAD_REQUEST)

        correct_choices = set(quiz_choices.filter(correct=True).values_list('id', flat=True))  # Correct choice UUIDs

        is_correct = submitted_choices == correct_choices

        performance, created = LearnerAssessmentStepPerformance.objects.get_or_create(
            learner=user,
            base_step=quiz_step.base_step,
            defaults={'passed': is_correct, 'attempts': 1}
        )

        if not created and not performance.passed:
            performance.attempts += 1
            performance.passed = is_correct
            performance.save()

        if is_correct:
            response_data = {'detail': 'Correct answer'}
        else:
            response_data = {'detail': 'Incorrect answer'}

        return Response(response_data, status=status.HTTP_200_OK)


class TextProblemView(APIView):
    permission_classes = [IsAuthenticated]

    def get_text_problem(self, pk, user):
        try:
            text_problem = TextProblemLessonStep.objects.get(
                base_step_id=pk,
                base_step__lesson__chapter__course__enrolled_learners=user
            )
        except TextProblemLessonStep.DoesNotExist:
            raise NotFound('Text problem not found')

        return text_problem

    def get(self, request, pk):
        user = request.user

        text_problem = self.get_text_problem(pk, user)
        course_id = text_problem.base_step.lesson.chapter.course_id

        learner_progress = LearnerProgress.objects.filter(learner=user, course_id=course_id).first()
        if not (learner_progress and text_problem.base_step_id in learner_progress.completed_steps):
            text_problem_data = TextProblemLessonStepSerializer(text_problem, context={'is_learner': True}).data
        else:
            text_problem_data = TextProblemLessonStepSerializer(text_problem).data

        return Response(text_problem_data)

    def post(self, request, pk):
        user = request.user

        answer = request.data.get('answer')
        if not answer:
            return Response({'error': 'answer is required'}, status=status.HTTP_400_BAD_REQUEST)

        text_problem = self.get_text_problem(pk, user)

        if text_problem.allow_regex:
            pattern = text_problem.correct_answer
            if not text_problem.case_sensitive:
                pattern = '(?i)' + pattern  # Adding case-insensitive flag to regex
            is_correct = bool(re.compile(pattern).match(answer))
        elif text_problem.case_sensitive:
            is_correct = answer == text_problem.correct_answer
        else:
            is_correct = answer.lower() == text_problem.correct_answer.lower()

        performance, created = LearnerAssessmentStepPerformance.objects.get_or_create(
            learner=user,
            base_step=text_problem.base_step,
            defaults={'passed': is_correct, 'attempts': 1}
        )

        if not created and not performance.passed:
            performance.attempts += 1
            performance.passed = is_correct
            performance.save()

        if is_correct:
            response_data = {'detail': 'Correct answer'}
        else:
            response_data = {'detail': 'Incorrect answer'}

        return Response(response_data, status=status.HTTP_200_OK)


class SortingStepView(APIView):
    permission_classes = [IsAuthenticated]

    def get_sorting_step(self, pk, user):
        try:
            sorting_step = SortingProblemLessonStep.objects.prefetch_related('options').get(
                base_step_id=pk,
                base_step__lesson__chapter__course__enrolled_learners=user
            )
        except SortingProblemLessonStep.DoesNotExist:
            raise NotFound('Sorting problem not found')

        return sorting_step

    def get(self, request, pk):
        user = request.user

        sorting_step = self.get_sorting_step(pk, user)
        course_id = sorting_step.base_step.lesson.chapter.course_id

        learner_progress = LearnerProgress.objects.filter(learner=user, course_id=course_id).first()
        if not (learner_progress and sorting_step.base_step_id in learner_progress.completed_steps):
            sorting_data = SortingProblemLessonStepSerializer(sorting_step, context={'is_learner': True}).data
        else:
            sorting_data = SortingProblemLessonStepSerializer(sorting_step).data

        return Response(sorting_data)

    def post(self, request, pk):
        user = request.user

        sorting_step = self.get_sorting_step(pk, user)

        answer = request.data.get('ordered_options')
        if not isinstance(answer, list) or not answer:
            return Response({'error': 'ordered_options must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure all elements are integers
        try:
            submitted_order = [int(order) for order in answer]
        except (ValueError, AttributeError):
            return Response({'error': 'All ordered options must be valid integers'}, status=status.HTTP_400_BAD_REQUEST)

        correct_order = list(sorting_step.options.values_list('id', flat=True))
        is_correct = submitted_order == correct_order

        performance, created = LearnerAssessmentStepPerformance.objects.get_or_create(
            learner=user,
            base_step=sorting_step.base_step,
            defaults={'passed': is_correct, 'attempts': 1}
        )

        if not created and not performance.passed:
            performance.attempts += 1
            performance.passed = is_correct
            performance.save()

        if is_correct:
            response_data = {'detail': 'Correct answer'}
        else:
            response_data = {'detail': 'Incorrect answer'}

        return Response(response_data, status=status.HTTP_200_OK)


def get_next_step(lesson_step):
    lesson = lesson_step.lesson
    chapter = lesson_step.lesson.chapter
    next_step = lesson.baselessonstep_set.filter(order=lesson_step.order + 1).first()
    if not next_step:
        next_lesson = chapter.lesson_set.filter(order=lesson.order + 1).first()
        if next_lesson:
            next_step = next_lesson.baselessonstep_set.first()
    if not next_step:
        course = chapter.course
        next_chapter = course.chapter_set.filter(creation_date__gt=chapter.creation_date).first()
        if next_chapter:
            next_step = next_chapter.lesson_set.first().baselessonstep_set.first()
        else:
            next_step = lesson_step

    return next_step


@api_view(['POST'])
def complete_lesson_step(request, step_id):
    user = request.user

    enrolled = BaseLessonStep.objects.filter(
        lesson__chapter__course__enrolled_learners=user
    ).exists()
    if not enrolled:
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    try:
        lesson_step = BaseLessonStep.objects.select_related('lesson__chapter').get(id=step_id)
        lesson = lesson_step.lesson
        chapter = lesson.chapter
    except BaseLessonStep.DoesNotExist:
        return Response({'detail': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

    learner_progress, created = LearnerProgress.objects.get_or_create(course_id=chapter.course_id, learner=user)
    if lesson_step.id not in learner_progress.completed_steps:
        learner_progress.completed_steps.append(lesson_step.id)
        related_lesson_steps = lesson.baselessonstep_set.values_list('id', flat=True)
        lesson_completed = set(related_lesson_steps).issubset(learner_progress.completed_steps)
        if lesson_completed:
            learner_progress.completed_lessons.append(lesson.id)
            related_lessons = chapter.lesson_set.values_list('id', flat=True)
            chapter_completed = set(related_lessons).issubset(learner_progress.completed_lessons)
            if chapter_completed:
                learner_progress.completed_chapters.append(chapter.id)

        if learner_progress.completion_ratio != 100.0:
            next_step = get_next_step(lesson_step)
            if next_step:
                learner_progress.last_stopped_step = next_step
                learner_progress.last_stopped_lesson = next_step.lesson
                learner_progress.last_stopped_chapter = next_step.lesson.chapter
        else:
            course_enrollment = CourseEnrollment.objects.get(course=chapter.course, learner=user)
            course_enrollment.completed = True
            course_enrollment.save()

    learner_progress.save()

    serializer = LearnerProgressSerializer(learner_progress)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['creation_date', 'rating']

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id)
        return Review.objects.filter(course=course)

    def perform_create(self, serializer):
        user = self.request.user
        course = get_object_or_404(Course, id=self.kwargs['course_id'])

        if not course.enrolled_learners.filter(id=user.id).exists():
            raise ValidationError({'error': 'to send a review, you must be enrolled in this course'})

        if course.instructor == user:
            raise ValidationError({'error': 'you cannot review your own course'})

        learner_progress = LearnerProgress.objects.get(learner=user, course=course)
        if learner_progress.completion_ratio < 80:
            raise ValidationError({'error': 'to send a review, complete more than 80% of the course'})

        serializer.save(course=course, learner=user)


class ReviewRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(course__enrolled_learners=self.request.user)

    def get_object(self):
        review_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=review_id)


@api_view(['GET'])
def get_user_course_review(request, course_id):
    user = request.user
    review = Review.objects.filter(course_id=course_id, learner=user).first()
    if not review:
        return Response({'detail': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ReviewSerializer(review)
    return Response(serializer.data, status=status.HTTP_200_OK)


class FavouriteCoursesListView(generics.ListAPIView, LearnerCourseViewMixin):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = self.request.user
        favourite_course_ids = (CourseEnrollment.objects
                                .filter(learner=user, favourite=True)
                                .values_list('course', flat=True))
        favourite_courses = Course.objects.filter(id__in=favourite_course_ids)

        serialized_courses = []
        for course in favourite_courses:
            course_data = self.get_course_data(course)
            serialized_courses.append(course_data)

        return Response(serialized_courses)

    def post(self, request, *args, **kwargs):
        action = request.data.get('action')
        course_id = request.data.get('course_id')

        if not course_id:
            return Response({'error': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_id = UUID(course_id)
        except ValueError:
            return Response({'error': 'Invalid course ID'}, status=status.HTTP_400_BAD_REQUEST)

        course_enrollment = CourseEnrollment.objects.filter(course_id=course_id, learner=request.user).first()

        if not course_enrollment:
            return Response({'error': 'You must be enrolled in this course to modify its favorite status'},
                            status=status.HTTP_400_BAD_REQUEST)

        if action == 'add':
            course_enrollment.favourite = True
            course_enrollment.save()
            return Response({'detail': 'Course added to favorites'}, status=status.HTTP_200_OK)
        elif action == 'remove':
            course_enrollment.favourite = False
            course_enrollment.save()
            return Response({'detail': 'Course removed from favorites'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_engagement_data(request):
    user = request.user

    step_id = request.data.get('step_id')
    if not step_id:
        return Response({'detail': 'step_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    step = get_object_or_404(BaseLessonStep, id=step_id)

    course = step.lesson.chapter.course
    if not course.enrolled_learners.filter(id=user.id).exists():
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    engagement, created = EngagementAnalytics.objects.get_or_create(learner=user, lesson_step=step,
                                                                    defaults={'course': course,
                                                                              'time_spent': timedelta()})
    seconds = int(request.data.get('time_spent', 0))
    duration = timedelta(seconds=seconds)
    engagement.time_spent += duration
    engagement.save()

    return Response({'detail': 'Engagement data sent'}, status=status.HTTP_200_OK)
