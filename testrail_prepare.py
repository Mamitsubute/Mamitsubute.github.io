import os
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

    def add_plan(self, project_id, entries):
        # https://docs.testrail.techmatrix.jp/testrail/docs/702/api/reference/plans/
        # POST index.php?/api/v2/add_plan/:project_id
        entries["name"] = datetime.now().strftime("%Y-%m-%d-%H-%M") + " MagicPod Test"
        response = self._client.send_post(
            'add_plan/'+str(project_id),entries)
        return response

TESTRAIL_URL = os.environ.get("TESTRAIL_URL")
TESTRAIL_USER = os.environ.get("TESTRAIL_USER")
TESTRAIL_PASSWORD = os.environ.get("TESTRAIL_PASSWORD")
TESTRAIL_TESTPLAN_JSON_FILENAME = './testplan.json'
TESTRAIL_PROJECT_ID = 3 # [ToDo]Change to the target project id in TestRail
TESTRAIL_TESTPLAN_ENTRY = {
    "name": "testplan_name",
    "entries": [
        {
            "suite_id": 3, # [ToDo]Change to the target suite_id in TestRail
            "include_all": True, # All test cases in a suite will be included in the test plan
            "config_ids": [5,6,7], # [ToDo]Change to the target config ids
            "runs": [
                {
                    "config_ids": [5] # [ToDo]Change to the target config id
                },
                {
                    "config_ids": [6] # [ToDo]Change to the target config id
                },
                {
                    "config_ids": [7] # [ToDo]Change to the target config id
                }
            ]
        },
    ]
}


def prepare_testplan():
    print("Preparing test plan")
    client = TestRailAPIWrapper(TESTRAIL_URL, TESTRAIL_USER, TESTRAIL_PASSWORD)
    response = client.add_plan(TESTRAIL_PROJECT_ID, TESTRAIL_TESTPLAN_ENTRY)
    print(json.dumps(response, indent=4))
    with open(TESTRAIL_TESTPLAN_JSON_FILENAME, "w", encoding='utf-8') as file:
        file.write(json.dumps(response))

prepare_testplan()