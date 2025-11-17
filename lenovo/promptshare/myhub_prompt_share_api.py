import logging
import unittest
from typing import Dict, Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

_log = logging.getLogger(__name__)


class myhub_prompt_share_restapi(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://localhost:8080/v2/cms/myai/promptshare"
        self.channel = "MyAINeiMeng"
        self.base_header = {
            'language': 'cn',
            'X-User-SiteId': '23',
            'Content-Type': 'application/json',
            'Authorization': "Bearer eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJsZW5vdm8iLCJzdWIiOiJqaWdzMiIsImlkIjo0MTYzNTMsInR5cGUiOiJzaXRlLXVzZXIiLCJleHAiOjE3NjMzNjg0NDAsImlhdCI6MTc2Mjc2MzY0MH0.sYrMkz0H4wnzaoIq-ilq1ctm3i91zIXw7_482Y-bUfXSj3lJUM7JDF5ZeiQuW4B71F68i5-J0e9aPtzOwnghHg"
        }

    def test_instruction_get(self):
        url = f"http://localhost:8080/v2/cms/aiHub/instruction/{self.channel}"
        payload = json.dumps({})
        headers = self.base_header
        response = requests.request("GET", url, headers=headers, data=payload)
        print(response.text)

    def test_personalkb_get(self):
        url = f"http://localhost:8080/v2/cms/myai/personalkb/list/{self.channel}?pageNo=1&pageSize=10"
        payload = json.dumps({})
        headers = self.base_header
        response = requests.request("GET", url, headers=headers, data=payload)
        print(response.text)

    def test_get_prompt_by_owner(self):
        url = f"{self.base_url}/list/{self.channel}"
        payload = json.dumps({})
        headers = self.base_header
        response = requests.request("GET", url, headers=headers, data=payload)
        print(response.text)

    def test_share_prompt(self):
        url = f"{self.base_url}/batch/share/execute/{self.channel}"
        payload = json.dumps({
            "shareTo": [
                {
                    "itCode": "jigs2",
                    "displayName": "jiguisong",
                    "email": "jigs2@lenovo.com"
                }
            ],
            "sharePromptList": [
                {
                    "personalInstructionId": 64
                },
                {
                    "personalInstructionId": 71
                },
                {
                    "personalInstructionId": 54
                }

            ],
            "shareMessage": "12312qweq\r\nqwerqwrwq未完全发过去问过我全国 、、、、、"
        })
        print(json.dumps(payload))
        headers = self.base_header
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)

    def test_delete_prompt(self):
        url = f"{self.base_url}/batch/delete/{self.channel}"
        payload = json.dumps({
            "personalInstructionIdList":[78,38]
        })
        headers = self.base_header
        response = requests.request("DELETE", url, headers=headers, data=payload)
        print(response.text)

    def test_myai_survey_encryptitcode(self):
        url = f"http://ecmp-site-bff.t-sy-in.earth.xcloud.lenovo.com/v2/cms/myai/survey/itcode/encrypt/{self.channel}"
        payload = json.dumps({})
        headers = self.base_header
        response = requests.request("GET", url, headers=headers, data=payload)
        print(response.text)


if __name__ == '__main__':
    unittest.main()
