from celery.result import AsyncResult
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from .serializers import LearnerCourseSerializer, CodeChallengeSubmissionSerializer
from courses.models import Course, CodeChallengeLessonStep
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

    def get_serializer_context(self):
        context = super().get_serializer_context()

        user = self.request.user
        courses = self.get_queryset()

        learner_progress_list = LearnerProgress.objects.filter(learner__user=user, course__in=courses)

        context.update({
            'learner_progress_list': learner_progress_list
        })
        return context


class LearnerCourseView(generics.RetrieveAPIView):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners__user=user)

    def get_object(self):
        course_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=course_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        learner = self.request.user

        learner_progress = LearnerProgress.objects.filter(learner=learner, course=self.get_object())

        context.update({
            'learner_progress': learner_progress
        })
        return context


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
    # TO DO CHANGE
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
