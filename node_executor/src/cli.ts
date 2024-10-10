// src/cli.ts
import { Command, program } from 'commander';
import axios, { AxiosError, AxiosProxyConfig, AxiosRequestConfig, AxiosResponse } from 'axios';
import { expect, AssertionError } from 'chai';
var _ = require('lodash');


interface TestCaseRequest {
    method: string;
    url: string;
    headers?: Record<string, string>;
    params?: Record<string, string>;
    data?: any;
}

// Function to run the request using Axios
async function runRequest(test_case_request: TestCaseRequest, proxy?: string): Promise<{
    request: AxiosRequestConfig,
    response: AxiosResponse | null | undefined,
    error: any
}> {
    try {
        const axiosConfig: AxiosRequestConfig = {
            method: test_case_request.method?.toLocaleLowerCase(),
            url: test_case_request.url,
            headers: test_case_request.headers,
            params: test_case_request.params,
            data: test_case_request.data,
            proxy: proxy ? { host: proxy } as AxiosProxyConfig : false
        };

        const response: AxiosResponse = await axios(axiosConfig);


        return {
            request: test_case_request,
            response: response,
            error: null
        }
    } catch (error) {
        return {
            request: test_case_request,
            response: {
                headers: (error as AxiosError).response?.headers as any,
                data: (error as AxiosError).response?.data,
                status: (error as AxiosError).response?.status as number,
                statusText: (error as AxiosError).response?.statusText as string
            } as AxiosResponse,
            error: error
        };
    }
}

function runAssertions(assertions: string[], response: any): { assertion: string, status: boolean, message: string }[] {
    const result: { assertion: string, status: boolean, message: string }[] = []
    for (const assertion of assertions) {
        try {
            // Directly use the assertion string with expect
            const assertionFunction = new Function('expect', 'response', 'AssertionError', `
                try {
                    ${assertion}
                    return { success: true, message: 'Assertion passed successfully!' };
                } catch (error) {
                    return { success: false, message: error instanceof AssertionError ? error.message : error.toString() };
                }
            `);
            const assertionResult = assertionFunction(expect, response, AssertionError);
            if (!assertionResult.success) {
                result.push({
                    assertion: assertion,
                    status: false,
                    message: `Assertion failed: ${assertionResult.message}`
                })
            } else {
                result.push({
                    assertion: assertion,
                    status: true,
                    message: `Assertion passed: ${assertionResult.message}`
                })
            }
        } catch (error: any) {
            result.push({
                assertion: assertion,
                status: false,
                message: `Assertion failed: ${error.message}`
            });
        }
    }
    return result;
}

function validateAndParseRequest(request?: string): TestCaseRequest | null {
    if (!request) {
        console.error('Error: Request string is required. Use --request option to provide a request string.');
        return null;
    }

    try {
        const parsedRequest: TestCaseRequest = JSON.parse(request);
        return parsedRequest;
    } catch (error) {
        console.error('Error: Request string is not properly formatted JSON. Use --request option to provide a request string.');
        return null
    }
}

function validateAndParseAssertions(tests?: string): string[] | null {
    if (!tests) {
        return null;
    }

    try {
        const parsedAssertions: string[] = tests.trim().split("\n");
        return parsedAssertions;
    } catch (error) {
        console.error('Error: tests string is not properly formatted JSON. Use --tests option to provide a test string.');
        return null
    }
}

function stringifyObject(obj: any) {
    if (_.isArray(obj) || !_.isObject(obj)) {
        return obj.toString()
    }
    var seen: any[] = [];
    return JSON.stringify(
        obj,
        function (key, val) {
            if (val != null && typeof val == "object") {
                if (seen.indexOf(val) >= 0)
                    return
                seen.push(val)
            }
            return val
        }
    );
}

program
    .version('1.0.0')
    .description('A CLI tool for testing requests and tests')
    .option('-r, --request <type>', 'Request string')
    .option('-t, --tests <type>', 'Tests string')
    .option('-p, --proxy <type>', 'Proxy url')
    .action(async () => {
        const options: { request?: string, tests?: string, proxy?: string } = program.opts();

        const requestStr = options.request;
        const parsedRequest = validateAndParseRequest(requestStr);
        if (!parsedRequest) return;
        const proxy = options.proxy;

        const { request, response, error } = await runRequest(parsedRequest, proxy);

        const tests = validateAndParseAssertions(options.tests);
        if (!tests) {
            console.log(stringifyObject({
                request: request,
                response: response,
                assertions: null
            }))
            return
        }
        const assertionsResult = runAssertions(tests, {
            "response": response?.data,
            "statusCode": response?.status,
            "error": error
        })
        console.log(stringifyObject({
            request: request,
            response: response,
            assertions: assertionsResult
        }),)
        return
    }).parse(process.argv);



