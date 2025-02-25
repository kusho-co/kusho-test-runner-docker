from pprint import pprint
import requests, time, json
import subprocess


def test_case_node_executor(request, assertions, proxy):
    # Construct the command
    command = ['./node_executor/node_executor', '-r', json.dumps(request)]
    if assertions:
        command.extend(['-t', assertions])
    if proxy:
        command.extend(['-p', proxy])

    # Execute the command
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        # Handle error if the subprocess returns a non-zero exit code
        print(f"Error: {e}")
        return {
                "request": request,
                "response": None,
                "assertions": None,
                "error": e
        }

def process_test_suites(data):
    results = []
    
    for test_suite in data:
        suite_result = {
            'test_suite_name': test_suite['test_suite_name'],
            'test_cases': []
        }
        
        for test_case in test_suite['test_cases']:
            try:
                test_case_request = test_case['api_info']
                environment = test_case.get('env', {})
                
                executed_data = test_case_node_executor(
                    test_case_request, 
                    test_case.get("assertions", ""), 
                    None
                )

                if "assertions" in test_case:
                    del test_case["assertions"]

                try:
                    all_assertions_passed = all(assertion['status'] for assertion in executed_data["assertions"])
                    assertion_status = "success" if all_assertions_passed else "fail"
                except Exception as e:
                    assertion_status = "N/A"

                test_case_result = {
                    "test_case": test_case,
                    "test_case_execution_status": "success",
                    "request": test_case_request, 
                    "response": executed_data["response"].get('status'),
                    "assertion_status": assertion_status
                }
            except Exception as e:
                print(f"Error in test case execution: {e}")
                test_case_result = {
                    "test_case": test_case, 
                    "test_case_execution_status": "error",
                    "response": None,
                    "assertion_status": "N/A"
                }

            suite_result['test_cases'].append(test_case_result)
        
        results.append(suite_result)
    
    return results

def format_output(data):
    headers = ["Description", "Status Code", "Test Status"]
    all_results = []

    for test_suite in data['result']:
        test_suite_name = test_suite['test_suite_name']
        results = []
        for item in test_suite['test_cases']:
            test_case = item['test_case']
            execution_status = item['assertion_status']
            execution_status_symbol = "Failed ✘" if execution_status == 'fail' else "N/A" if execution_status == 'N/A' else "Passed ✔"
            api_status_code = item['response']

            result = [
                test_case['api_info']['test_case_desc'],
                api_status_code or None,
                execution_status_symbol
            ]
            results.append(result)
        
        all_results.append((test_suite_name, results))
    
    return headers, all_results
