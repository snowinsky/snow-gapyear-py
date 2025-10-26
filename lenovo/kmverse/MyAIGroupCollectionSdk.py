import logging
import ssl
from typing import Dict, Any, Optional, Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lenovo.apihub.ApiHubTokenGetter import sync_get_api_hub_token_for_myai

_log = logging.getLogger(__name__)

# ------------------全局常量------------------
CONN_TIMEOUT = 5  # TCP建连超时(s)
READ_TIMEOUT = 20  # socket读超时(s)
MAX_RETRIES = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504])
POOL_SIZE = 100  # pool_connections/pool_maxsize

class MyAIGroupCollectionSdk:
    """
    requests-based、线程安全的 HTTP Client。
    """

    def __init__(self,
                 base_url: str,
                 api_key: str,
                 token_client):
        """
        """

        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.token_fn: Callable[[], Dict[str, Any]] = token_client

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

    def _fresh_access_token(self) -> str:
        """线程安全地刷新 access_token"""
        payload = self.token_fn()
        token = payload['access_token']
        _log.debug("access_token  refreshed %s...", token[:8])
        return token

    def send_request(self,
                     url_no_params: str,
                     json_params: Optional[Dict[str, Any]] = None,
                     method: str = 'GET',
                     json_body: Optional[Dict] = None) -> str:
        """
        sync发送 HTTP(s)请求并返回 response.text 。
        """
        url = f"{self.base_url}/kb/api/myai/v1/knowledge-base/personalkb{url_no_params}"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-API-KEY": self.api_key,
            "Authorization": f"Bearer {self._fresh_access_token()}",
        }

        _log.info("%s  %s", method.upper(), url)
        _log.info("json_params %s", json_params)
        _log.info("json_body %s", json_body)

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

    def call_qa_api_getKbListByItCode(self, itcode, channel) -> str:
        """
        获取客户可访问的所有知识库
        :return: str
        """
        return self.send_request('/qa/knowledgeBase/list', method='POST', json_body={
            'itCode': itcode,
            'channel': channel,
            'pageNo': 1,
            'pageSize': 200
        })

    def call_qa_api_hasPermission(self, itcode, channel, kbId) -> str:
        """
        判断客户是否对该知识库有权限
        :return: str
        """
        return self.send_request('/qa/knowledgeBaseId/hasPermission', method='POST', json_body={
            'itCode': itcode,
            'channel': channel,
            'kbId': kbId
        })

    def call_qa_api_getBindStatus(self, sessionId) -> str:
        """
        查看绑定状态
        :return: str
        """
        return self.send_request('/qa/knowledgeBaseId/bind/check', method='POST', json_body={
            'sessionId': sessionId
        })

    def call_qa_api_bindSessionAndKbId(self, itCode, channel, sessionId, kbId) -> str:
        """
        绑定知识库
        :return: str
        """
        return self.send_request('/qa/knowledgeBaseId/bind', method='POST', json_body={
            'itCode': itCode,
            'channel': channel,
            'sessionId': sessionId,
            'kbId': kbId
        })

    def call_qa_api_unbindSessionAndKbId(self, itCode, channel, sessionId, kbId) -> str:
        """
        解绑知识库
        :return: str
        """
        return self.send_request('/qa/knowledgeBaseId/unbind', method='POST', json_body={
            'itCode': itCode,
            'channel': channel,
            'sessionId': sessionId,
            'kbId': kbId
        })

    def call_qa_api_searchKbId(self, itCode, channel, query, kbId) -> str:
        """
        检索知识库
        :return: str
        """
        return self.send_request('/qa/knowledgeBase/retrieval', method='POST', json_body={
            {
                "query": query,
                "knowledgeBaseId": kbId,
                "similarityTopK": 3,
                "itCode": itCode,
                "channel": channel
            }
        })


def apihub_call_myai_group_collection():
    client = MyAIGroupCollectionSdk(
        base_url="https://apihub-test.lenovo.com/sit/v1.0/services/myai",
        api_key="AxZIlOysxxgDaGIt0wOIaOpFHH4EnO6C",
        token_client=lambda: sync_get_api_hub_token_for_myai())
    return client

if __name__ == '__main__':
    client = apihub_call_myai_group_collection()
    res = client.call_qa_api_getKbListByItCode('jigs2', 'LeAI')
    print(res)

