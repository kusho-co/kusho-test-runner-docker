import os
import requests
import json
import pandas as pd
from tabulate import tabulate
from typing import Dict, Any, Optional
from api_execution import process_test_suites, format_output

# Define URL constants
BASE_URL = os.getenv("BASE_URL", "https://be.kusho.ai")
if BASE_URL[-1] == "/":  # remove ending slash
    BASE_URL = BASE_URL[:-1]
TEST_DATA_FETCH_URL = f"{BASE_URL}/run/test-suite/metadata"
POST_PROCESS_URL = f"{BASE_URL}/run/test-suite/post-process"

def get_env_var(var_name: str, required: bool = True) -> Optional[str]:
    value = os.environ.get(var_name)
    if required and not value:
        raise ValueError(f"Environment variable {var_name} must be set")
    return value

def make_api_request(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def call_api_for_uuid(uuid: str, environment_id: str, api_key: str) -> Dict[str, Any]:
    payload = {
        "environment_id": environment_id,
        "test_suite_uuid": uuid
    }
    headers = {
        'API-KEY': api_key,
        'Content-Type': 'application/json',
    }
    return make_api_request(TEST_DATA_FETCH_URL, payload, headers)

def call_api() -> Dict[str, Any]:
    test_suite_uuids = get_env_var('TEST_SUITE_UUID', required=False)
    group_id = get_env_var('GROUP_ID', required=False)
    environment_id = get_env_var('ENVIRONMENT_ID')
    api_key = get_env_var('API_KEY')
    tags = get_env_var('TAGS', required=False)

    if not (test_suite_uuids or group_id or tags):
        raise ValueError("Either TEST_SUITE_UUID, GROUP_ID or TAGS must be set")

    all_results = []

    if group_id:
        # Handle group_id case (unchanged)
        payload = {"environment_id": environment_id, "group_id": group_id}
        headers = {
            'API-KEY': api_key,
            'Content-Type': 'application/json',
        }
        metadata = make_api_request(TEST_DATA_FETCH_URL, payload, headers)
        all_results.extend(metadata.get('result', []))
    elif tags:
        # Handle multiple tags
        tags = [t.strip() for t in tags.split(",")]
        tags = [t for t in tags if t]  # remove empty values
        payload = {"environment_id": environment_id, "tags": tags}
        headers = {
            'API-KEY': api_key,
            'Content-Type': 'application/json',
        }
        metadata = make_api_request(TEST_DATA_FETCH_URL, payload, headers)
        all_results.extend(metadata.get('result', []))
    elif test_suite_uuids:
        # Handle multiple UUIDs
        uuid_list = [uuid.strip() for uuid in test_suite_uuids.split(',')]
        for uuid in uuid_list:
            metadata = call_api_for_uuid(uuid, environment_id, api_key)
            all_results.extend(metadata.get('result', []))

    processed_results = process_test_suites(all_results)
    return {"result": processed_results}

def test_suite_execution_post_processing(test_data: Dict[str, Any]) -> Dict[str, Any]:
    email = get_env_var('EMAIL', required=False)
    api_key = get_env_var('API_KEY')
    commit_info = {
        "commit_hash": get_env_var("CI_COMMIT_SHA", required=False),
        "commit_message": get_env_var("CI_COMMIT_MESSAGE", required=False)
    }

    payload = {
        "test_data": test_data,
        "email": email,
        "commit_info": commit_info
    }

    headers = {
        'API-KEY': api_key,
        'Content-Type': 'application/json',
    }

    return make_api_request(POST_PROCESS_URL, payload, headers)

def display_results(headers: list, all_results: list) -> None:
    colalign = ["left"] * len(headers)  # Apply left alignment for all columns
    for suite_name, results in all_results:
        print(f"\n{suite_name}")
        print(tabulate(results, headers, tablefmt="pretty", colalign=colalign))
        print("\n" + "="*50 + "\n")  # Separator between tables

def main() -> None:
    try:
        data = call_api()
        headers, all_results = format_output(data)
        display_results(headers, all_results)
        test_suite_execution_post_processing(test_data=data)
        for test_suite in data["result"]:
            for test_case in test_suite["test_cases"]:
                if test_case["assertion_status"] == "fail":
                    exit(1)  # exit with status 1 if any test case fails
        exit(0)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
