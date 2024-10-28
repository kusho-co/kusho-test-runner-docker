import os
import requests
import json
import pandas as pd
from tabulate import tabulate
from typing import Dict, Any, Optional
from api_execution import process_test_suites, format_output

# Define URL constants
API_URL = "https://be.kusho.ai/run/test-suite-metadata"
EMAIL_URL = "https://be.kusho.ai/run/test-suite-email"

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
    return make_api_request(API_URL, payload, headers)

def call_api() -> Dict[str, Any]:
    test_suite_uuids = get_env_var('TEST_SUITE_UUID', required=False)
    group_id = get_env_var('GROUP_ID', required=False)
    environment_id = get_env_var('ENVIRONMENT_ID')
    api_key = get_env_var('API_KEY')

    if not (test_suite_uuids or group_id):
        raise ValueError("Either TEST_SUITE_UUID or GROUP_ID must be set")

    all_results = []

    if group_id:
        # Handle group_id case (unchanged)
        payload = {"environment_id": environment_id, "group_id": group_id}
        headers = {
            'API-KEY': api_key,
            'Content-Type': 'application/json',
        }
        metadata = make_api_request(API_URL, payload, headers)
        all_results.extend(metadata.get('result', []))
    elif test_suite_uuids:
        # Handle multiple UUIDs
        uuid_list = [uuid.strip() for uuid in test_suite_uuids.split(',')]
        for uuid in uuid_list:
            metadata = call_api_for_uuid(uuid, environment_id, api_key)
            all_results.extend(metadata.get('result', []))

    processed_results = process_test_suites(all_results)
    return {"result": processed_results}

def send_test_suite_report_email(test_data: Dict[str, Any]) -> Dict[str, Any]:
    email = get_env_var('EMAIL', required=False)
    api_key = get_env_var('API_KEY')

    if not email:
        print("Email not provided. Skipping email report.")
        return {}

    payload = {
        "test_data": test_data,
        "email": email
    }

    headers = {
            'API-KEY': api_key,
            'Content-Type': 'application/json',
        }

    return make_api_request(EMAIL_URL, payload, headers)

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
        send_test_suite_report_email(test_data=data)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()