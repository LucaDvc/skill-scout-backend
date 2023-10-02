import time

import requests
from django.db import transaction
from django.core.cache import cache

from courses.models import CodeChallengeLessonStep
from learning.api.serializers import CodeChallengeSubmissionSerializer
from learning.models import CodeChallengeSubmission, TestResult
from learning.utils import batch_queryset

from celery import shared_task
from courses import judge0_service


@shared_task(bind=True, max_retries=3)
def evaluate_code(self, code, code_challenge_step_id, learner_id, continue_on_error=False):
    """
    Evaluates the code by sending batch submissions containing the test cases to the judge0 api.
    Creates or updates related db objects: CodeChallengeSubmission and TestResult.

    :param self: celery param
    :param code: submission code string
    :param code_challenge_step_id: id of related CodeChallengeLessonStep object
    :param learner_id: id of related Learner object
    :param continue_on_error: flag for continuing submission processing upon receiving a judge0 code execution error
    :return: CodeChallengeSubmission object
    """
    # create batches as max batch size for judge0 call is 20
    code_challenge_step = cache.get(f'code_challenge_{code_challenge_step_id}')
    if not code_challenge_step:
        code_challenge_step = CodeChallengeLessonStep.objects.get(base_step_id=code_challenge_step_id)
    test_cases = code_challenge_step.test_cases.all()
    with transaction.atomic():
        code_challenge_submission, created = CodeChallengeSubmission.objects.get_or_create(
            learner_id=learner_id,
            code_challenge_step_id=code_challenge_step_id
        )
        code_challenge_submission.submitted_code = code
        code_challenge_submission.error_message = None
        code_challenge_submission.save()
    print('before batching')
    batch_size = 20
    batches = batch_queryset(test_cases, batch_size)
    for batch in batches:
        token_to_testresult_mapping = {}
        submissions = []
        test_results_batch = []
        for test_case in batch:
            test_result, created = TestResult.objects.get_or_create(
                submission=code_challenge_submission,
                test_case=test_case
            )
            test_results_batch.append(test_result)
            print(test_result)
            submission = {
                "source_code": code,
                "language_id": code_challenge_step.language_id,
                "stdin": test_case.input,
                "expected_output": test_case.expected_output
            }

            submissions.append(submission)

        batch_submission_response = judge0_service.submit_batch(submissions)
        submission_tokens = [submission['token'] for submission in batch_submission_response]
        print(submission_tokens)

        for token, test_result in zip(submission_tokens, test_results_batch):
            token_to_testresult_mapping[token] = test_result

        print(token_to_testresult_mapping)
        # call judge0 api to check batch results (with the tokens)
        # Set up a loop to poll the Judge0 API for the results
        max_retries = 5
        retries = 0
        all_results_received = False
        while not all_results_received and retries < max_retries:
            tokens_to_remove = []
            all_results_received = True
            try:
                result = judge0_service.get_batch_submission_result(submission_tokens)
                print(result)
            except requests.HTTPError as e:
                print(str(e))
                retries += 1
                all_results_received = False
                continue
            submissions = result.get('submissions', [])
            print('iterating submissions')
            for submission in submissions:
                print(submission)
                status = submission.get('status', {}).get('description', '')
                if status not in ['In Queue', 'Processing']:
                    token = submission.get('token', '')
                    print(token)
                    tokens_to_remove.append(token)
                    test_result = token_to_testresult_mapping[token]
                    test_result.status = status
                    test_result.stdout = submission.get('stdout', None)
                    test_result.stderr = submission.get('stderr', None)
                    test_result.compile_err = submission.get('compile_output', None)
                    if status == 'Accepted':
                        test_result.passed = True
                    else:
                        test_result.passed = False
                    test_result.save()

                    if test_result.stderr or test_result.compile_err:
                        code_challenge_submission.error_message = f"Error: {test_result.stderr or test_result.compile_err}"
                        code_challenge_submission.passed = False
                        print(f"Error encountered: {code_challenge_submission.error_message}")
                        if not continue_on_error:
                            print("Stopping further processing due to error")
                            code_challenge_submission.save()
                            return CodeChallengeSubmissionSerializer(code_challenge_submission).data
                else:
                    all_results_received = False  # Not all results are received, continue polling
                    retries += 1
                    break

            submission_tokens = [token for token in submission_tokens if token not in tokens_to_remove]
            time.sleep(2)

        if not all_results_received:
            raise self.retry(countdown=2)

    code_challenge_submission.update_passed_status()
    return CodeChallengeSubmissionSerializer(code_challenge_submission).data