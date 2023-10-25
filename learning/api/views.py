from celery.result import AsyncResult
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from .serializers import LearnerCourseSerializer, LearnerProgressSerializer
from courses.models import Course, CodeChallengeLessonStep, BaseLessonStep
from rest_framework.permissions import IsAuthenticated

from learning.models import LearnerProgress
from learning.tasks import evaluate_code
from celery import states
from django.core.cache import cache


class LearnerCourseListView(generics.ListAPIView):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners__user=user)


class LearnerCourseView(generics.RetrieveAPIView):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners__user=user)

    def get_object(self):
        course_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=course_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_code_challenge(request, pk):
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
                base_step__lesson__chapter__course__instructor__user=user
            )
        else:
            # Check if the user is enrolled in the course associated with this code challenge
            code_challenge_step = code_challenge_step.get(
                base_step_id=pk,
                base_step__lesson__chapter__course__enrolled_learners__user=user
            )

    except CodeChallengeLessonStep.DoesNotExist:
        # Code challenge step does not exist or the user does not have the required role
        return Response({'detail': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

    code_challenge_id = code_challenge_step.base_step_id
    cache.set(f'code_challenge_{code_challenge_id}', code_challenge_step, timeout=300)
    is_instructor = (acting_role == 'instructor')
    task = evaluate_code.delay(code, code_challenge_id, user.learner.id, is_instructor)

    return Response({"token": str(task.id)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_code_challenge_result(request, task_id):
    user = request.user
    enrolled = CodeChallengeLessonStep.objects.filter(
        base_step__lesson__chapter__course__enrolled_learners__user=user
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
            exception = result.result
            response_data = {
                'task_status': states.FAILURE,
                'error': exception
            }
            return Response(response_data)
    else:
        return Response({'status': states.PENDING})


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
        lesson__chapter__course__enrolled_learners__user=user
    ).exists()
    if not enrolled:
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    try:
        lesson_step = BaseLessonStep.objects.select_related('lesson__chapter').get(id=step_id)
        lesson = lesson_step.lesson
        chapter = lesson.chapter
    except BaseLessonStep.DoesNotExist:
        return Response({'detail': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

    learner_progress, created = LearnerProgress.objects.get_or_create(course_id=chapter.course_id, learner=user.learner)
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

    learner_progress.save()

    serializer = LearnerProgressSerializer(learner_progress)

    return Response(serializer.data, status=status.HTTP_201_CREATED)
