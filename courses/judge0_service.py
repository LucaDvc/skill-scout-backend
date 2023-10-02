import requests
from django.conf import settings

BASE_URL = settings.JUDGE0_HOST
X_AUTH_TOKEN = settings.JUDGE0_AUTH_TOKEN
X_AUTH_USER = settings.JUDGE0_AUTH_USER


def get_languages():
    headers = {
        'X-Auth-Token': X_AUTH_TOKEN
    }
    response = requests.get(f"{BASE_URL}/languages", headers=headers)
    if response.status_code != 200:
        raise requests.HTTPError("Failed to fetch languages from Judge0 API.")

    return response.json()


def submit_batch(submissions):
    """
    Make a batch submission request to the judge0 API.
    :param submissions: List of base64 encoded code submissions
    :return: API response containing a list of tokens for each submission
    """
    headers = {
        'X-Auth-Token': X_AUTH_TOKEN,
        'Content-Type': 'application/json',
    }
    body = {
        "submissions": submissions
    }
    print('judge0_service.submit_batch body = ' + str(body))
    # Batch submission, base64 encoded
    response = requests.post(
        f"{BASE_URL}/submissions/batch?base64_encoded=true&wait=false",
        headers=headers,
        json=body  # set the request body to a JSON serialization of the entire list
    )
    print('judge0_service.submit_batch response = ' + str(response))
    if response.status_code != 201:
        raise requests.HTTPError(f"Failed to create batch submission with the Judge0 API. Status code {response.status_code}")

    return response.json()


def get_submission_result(token):
    headers = {
        'X-Auth-Token': X_AUTH_TOKEN,
    }
    response = requests.get(f"{BASE_URL}/submissions/{token}?base64_encoded=true", headers=headers)
    if response.status_code != 200:
        raise requests.HTTPError(f"Failed to fetch submission result from Judge0 API. Status code {response.status_code}.")

    return response.json()


def get_batch_submission_result(tokens_list):
    headers = {
        'X-Auth-Token': X_AUTH_TOKEN,
        'X-Auth-User': X_AUTH_USER,
    }
    tokens = ",".join(tokens_list)
    print('judge0_service.get_batch_submission_result tokens = ' + tokens)
    url = f"{BASE_URL}/submissions/batch?tokens={tokens}&base64_encoded=true"
    print('judge0_service.get_batch_submission_result url = ' + url)
    response = requests.get(url, headers=headers)
    print('judge0_service.get_batch_submission_result response = ' + str(response))
    if response.status_code != 200:
        raise requests.HTTPError(f"Failed to fetch batch submission result from Judge0 API. Status code {response.status_code}.")

    return response.json()
