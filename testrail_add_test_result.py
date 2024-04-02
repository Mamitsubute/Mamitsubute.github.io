import os
import re
import sys
import base64
import json
import requests
import argparse
from datetime import datetime
from testrail import *

class TestRailAPIWrapper:

    def __init__(self, base_url, user, password):
        self._client = APIClient(base_url)
        self._client.user = user
        self._client.password = password

    def get_tests(self, run_id):
        # https://docs.testrail.techmatrix.jp/testrail/docs/702/api/reference/tests/
        # GET index.php?/api/v2/get_tests/:run_id
        response = self._client.send_get(
            'get_tests/'+str(run_id))
        return response['tests']

    def add_result(self, test_id, entries):
        # https://docs.testrail.techmatrix.jp/testrail/docs/702/api/reference/results/
        response = self._client.send_post(
            'add_result/'+str(test_id),entries)
        return response

TESTRAIL_URL = os.environ.get("TESTRAIL_URL")
TESTRAIL_USER = os.environ.get("TESTRAIL_USER")
TESTRAIL_PASSWORD = os.environ.get("TESTRAIL_PASSWORD")
TESTRAIL_TESTPLAN_JSON_FILENAME = './testplan.json'

def add_result(json_filename):
    print(f"Adding result using JSON file: {json_filename}")

    if not os.path.exists(json_filename):
        print("Error: json file not found.")
        sys.exit(1)

    if not os.path.exists(TESTRAIL_TESTPLAN_JSON_FILENAME):
        print("Error: testplan file not found.")
        sys.exit(1)
    
    with open(TESTRAIL_TESTPLAN_JSON_FILENAME, "r") as f:
        testplan_data = json.load(f)
        print(json.dumps(testplan_data, indent=4))
    
    with open(json_filename, "r") as f:
        magicpod_result_data = json.load(f)
        print(json.dumps(magicpod_result_data, indent=4))

    client = TestRailAPIWrapper(TESTRAIL_URL, TESTRAIL_USER, TESTRAIL_PASSWORD)

    # testrun
    is_succeed = 0
    magicpod_patterns = magicpod_result_data['test_cases']['details']
    i = 0
    entries = testplan_data['entries']
    for magicpod_pattern in magicpod_patterns:
        for entry in entries:
            testruns = entry['runs']
            for testrun in testruns:
                # testrunとmagicpodの結果をマッピング（ブラウザ名で特定）し、テストランIDを特定
                if testrun['config'] == magicpod_pattern['pattern_name']:
                    testrun_id = testrun['id']
                    # テストランIDからテストを取得
                    tests = client.get_tests(testrun_id)
                    for test in tests:
                        # TestRailのカスタムフィールドcustom_magicpod_urlでテストケースIDを特定、MagicPodの実行結果のtest_case.numberと突合する
                        pattern = r"\/(\d+)\/$"
                        test_case_id = re.search(pattern, test['custom_magicpod_url']).group(1)
                        results = magicpod_pattern['results']
                        for result in results:
                            if int(test_case_id) == int(result['test_case']['number']):
                                # 登録用のデータ整形
                                if result['status'] == "succeeded":
                                    status = 1
                                elif result['status'] == "failed":
                                    status = 5
                                
                                started_at = datetime.fromisoformat(result['started_at'])
                                if result['finished_at'] == "":
                                    finished_at = datetime.fromisoformat(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                                else:
                                    finished_at = datetime.fromisoformat(result['finished_at'])
                                elapsed_seconds = str((finished_at - started_at).total_seconds()) + "s"

                                comment = f"MagicPod URL:{magicpod_result_data['url']}"

                                result_data = {
                                    "status_id": status,
                                    "comment": comment,
                                    "elapsed": elapsed_seconds,
                                }

                                # 登録
                                add_result_response = client.add_result(test['id'], result_data)
                                print(json.dumps(add_result_response, indent=4))
        i += 1

add_result('./magicpod_result')