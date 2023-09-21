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
