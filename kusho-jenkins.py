import os
import requests
import json
import pandas as pd
from tabulate import tabulate
from api_execution import process_test_suites, format_output

def call_api():
    url = "https://be.kusho.ai/run/test-suite-metadata"
    
    # Read environment variables
    test_suite_uuid = os.environ.get('TEST_SUITE_UUID')
    environment_id = os.environ.get('ENVIRONMENT_ID')
    api_key = os.environ.get('API_KEY')
    group_id = os.environ.get('GROUP_ID')

    
    if not (test_suite_uuid or group_id):
        raise ValueError("Either TEST_SUITE_UUID or GROUP_ID must be set")

    # Prepare the payload based on the available environment variables
    payload = {
        "environment_id": environment_id
    }

    if group_id:
        payload["group_id"] = group_id
    elif test_suite_uuid:
        payload["test_suite_uuid"] = test_suite_uuid

    payload = json.dumps(payload)
    headers = {
        'API-KEY': api_key,
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

    metadata = response.json()

    processed_results = process_test_suites(metadata.get('result'))

    return {"result": processed_results}


def send_test_suite_report_email(test_data):
    url = "https://be.kusho.ai/run/test-suite-email"
    
    # Read the email from environment variables
    email = os.environ.get('EMAIL', None)

    if not email:
        raise ValueError("Environment variable EMAIL must be set")
    
    payload = {
        "test_data": test_data,
        "email": email
    }

    payload = json.dumps(payload)
    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        raise Exception(f"Email API call failed with status code {response.status_code}: {response.text}")

    return response.json()

def main():
    try:
        data = call_api()
        headers, all_results = format_output(data)
        
        for suite_name, results in all_results:
            print(f"\n{suite_name}")
            print(tabulate(results, headers, tablefmt="pretty"))
            print("\n" + "="*50 + "\n")  # Separator between tables
        
        send_test_suite_report_email(test_data=data)
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()