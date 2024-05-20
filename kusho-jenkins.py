import os
import requests
import json
import pandas as pd
from tabulate import tabulate

def call_api():
    url = "https://be.kusho.ai/run/test_suite"

    # Read environment variables
    test_suite_uuid = os.environ.get('TEST_SUITE_UUID')
    environment_id = os.environ.get('ENVIRONMENT_ID')
    api_key = os.environ.get('API_KEY')

    payload = json.dumps({
        "test_suite_uuid": test_suite_uuid,
        "environment_id": environment_id
    })
    headers = {
        'API-KEY': api_key,
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    data = response.json()

    # Check if environment variables are set
    if not all([test_suite_uuid, environment_id, api_key]):
        raise ValueError("Environment variables TEST_SUITE_UUID, ENVIRONMENT_ID, and API_KEY must be set")
    
    if response.status_code != 200:
        raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

    return data

def format_output(data):
    # Extract relevant data for tabular display
    headers = ["Description","Status Code", "Test Status"]
    results = []
    for item in data['result']:
        test_case = item['test_case']
        execution_status = item['assertion_status']
        execution_status_symbol = "Failed ✘" if execution_status == 'fail' else "Passed ✔"  
        api_status_code = item['response']

        result = [
            test_case['test_case_desc'],
            api_status_code or None,
            execution_status_symbol
        ]
        results.append(result)
    
    return headers, results

def main():
    try:
        data = call_api()
        headers, results = format_output(data)
        print(tabulate(results, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
