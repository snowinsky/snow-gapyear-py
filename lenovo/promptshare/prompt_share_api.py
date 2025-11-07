import logging
from typing import Dict, Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_log = logging.getLogger(__name__)

# ------------------全局常量------------------
CONN_TIMEOUT = 5  # TCP建连超时(s)
READ_TIMEOUT = 20  # socket读超时(s)
MAX_RETRIES = Retry(
    total=1,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504])
POOL_SIZE = 100


class prompt_share_restapi:

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        # ----构建 session----
        self.session: requests.Session = self._build_session()

    def _build_session(self) -> requests.Session:
        sess = requests.Session()

        adapter_kwargs = dict(max_retries=MAX_RETRIES)
        sess.mount('https://', HTTPAdapter(pool_connections=POOL_SIZE,
                                           pool_maxsize=POOL_SIZE,
                                           **adapter_kwargs))
        sess.mount('http://', HTTPAdapter(pool_connections=POOL_SIZE,
                                          pool_maxsize=POOL_SIZE,
                                          **adapter_kwargs))

        sess.verify = False  # trust all certs (prod谨慎!)

        return sess

    def send_request(self,
                     url_no_params: str,
                     json_params: Optional[Dict[str, Any]] = None,
                     method: str = 'GET',
                     json_body: Optional[Dict] = None) -> str:
        """
        sync发送 HTTP(s)请求并返回 response.text 。
        """
        url = f"{self.base_url}/api/myai/v1/personal-instruction/share{url_no_params}"

        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

        _log.info("http_method=%s  url=%s", method.upper(), url)

        resp = self.session.request(method.upper(),
                                    url,
                                    params=json_params,
                                    headers=headers,
                                    json=json_body,
                                    timeout=(CONN_TIMEOUT, READ_TIMEOUT))

        resp.raise_for_status()  # HTTP错误抛异常

        body_text = resp.text

        _log.debug("response  body:%s", body_text[:200])

        return body_text

    def close(self):
        """优雅关闭连接池"""
        self.session.close()

    def get_prompt_by_owner(self, itcode: str, lang: str) -> str:
        return self.send_request('/list', method='POST', json_body={
            "itCode": itcode,
            "channel": "LeAI",
            "language": lang})

    def share_prompt(self, fromMail: str, toMailList: list[str], idList: list[int], shareMessage=None) -> str:
        return self.send_request('/batch/share/execute',
                                 method='POST',
                                 json_body={
                                     "itCode": fromMail.split('@')[0],
                                     "channel": "LeAI",
                                     "shareFrom": {
                                         "itCode": fromMail.split('@')[0],
                                         "displayName": fromMail.split('@')[0] + 'fullName',
                                         "email": fromMail
                                     },
                                     "shareTo": [
                                         {
                                             "itCode": mail.split('@')[0],
                                             "displayName": mail.split('@')[0] + '_fullname',
                                             "email": mail
                                         }
                                         for mail in toMailList
                                         if '@' in mail
                                     ],
                                     "sharePromptList": [
                                         {
                                             "personalInstructionId": id
                                         }
                                         for id in idList
                                     ],
                                     "shareMessage": shareMessage
                                 })

    def delete_prompt(self, ids: list[int]) -> str:
        return self.send_request('/batch/share/delete', method='POST', json_body={
            "itCode": "sa",
            "channel": "LeAI",
            "language": "en",
            "ids": ids
        })