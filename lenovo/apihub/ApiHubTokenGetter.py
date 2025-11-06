# pip install aiohttp python-logging-ratelimit tenacity
import asyncio
import json
import ssl
import logging
import os
from typing import Dict, Any

import aiohttp
from aiohttp import ClientTimeout, ClientSession
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

_log = logging.getLogger(__name__)

# -------------------- 全局生产级配置 --------------------
CONNECT_TIMEOUT = 5  # TCP 建立连接超时
TOTAL_TIMEOUT = 10  # 完整请求超时
POOL_LIMIT = 100  # 连接池最大数
RETRY_TIMES = 1  # 重试次数

# TLS：如需自定义 CA / 跳过校验，可在此处构造 ssl_context
SSL_CONTEXT = None  # aiohttp.TCPConnector(ssl=False) 即可跳过证书校验


class ApiHubTokenGetter:
    """线程安全、可复用的高性能 TokenClient"""

    def __init__(self,
                 token_url: str,
                 api_key: str,
                 username: str,
                 password: str):
        self._token_url = token_url
        self._api_key = api_key
        self._username = username
        self._password = password

        # connector & timeout
        self._session: ClientSession | None = None

    def _ensure_session(self) -> ClientSession:
        """惰性创建 Session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=POOL_LIMIT, verify_ssl=False)
            timeout = ClientTimeout(total=TOTAL_TIMEOUT,
                                    connect=CONNECT_TIMEOUT)
            self._session = ClientSession(connector=connector,
                                          timeout=timeout)
        return self._session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """优雅关闭连接池"""
        await self._session.close()

        # -------------------- 核心方法 --------------------

    @retry(stop=stop_after_attempt(RETRY_TIMES),
           wait=wait_exponential_jitter(initial=0.5))
    async def get_api_token_async(self) -> Dict[str, Any]:
        """异步获取 token"""
        self._ensure_session()
        headers = {
            "X-API-KEY": self._api_key,
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = f"username={self._username}&password={self._password}"

        _log.info("getAPIHToken  for username=%s", self._username)

        async with self._session.post(self._token_url,
                                      data=payload,
                                      headers=headers) as resp:
            resp.raise_for_status()
            body_text = await resp.text()
            _log.info("getAPIHToken body=%s", body_text)
            return json.loads(body_text)

            # -------------------- 同步包装 --------------------

    def get_api_token(self) -> Dict[str, Any]:
        """同步调用入口，兼容旧代码"""
        return asyncio.run(self.get_api_token_async())

    def get_api_access_token(self) -> str:
        return asyncio.run(self.get_api_token_async())["access_token"]

        # -------------------- Usage Example --------------------


async def async_get_api_hub_token_for_kmverse() -> Dict[str, Any]:
    """
    接口洞察里的：apih_myai_token
    :return:
    """
    logging.basicConfig(level=logging.INFO)
    client = ApiHubTokenGetter(token_url='https://apihub-test.lenovo.com/token',
        api_key='L6Mf5DHsdEl6tfKKG01PKUkYzHI2zaaH',
         username='api_myai_app',
         password='H9-3(x$R5a')
    token_json = await client.get_api_token_async()
    await client.close()
    return token_json

async def async_get_api_hub_token_for_myai() -> Dict[str, Any]:
    """
    接口洞察里没有找到：
    :return:
    """
    logging.basicConfig(level=logging.INFO)
    client = ApiHubTokenGetter(token_url='https://apihub-test.lenovo.com/token',
                               api_key='AxZIlOysxxgDaGIt0wOIaOpFHH4EnO6C',
                               username='api_myhub_search',
                               password='j)t_nX002J')
    token_json = await client.get_api_token_async()
    await client.close()
    return token_json

async def async_get_api_hub_token_for_myhubbackend() -> Dict[str, Any]:
    """
    接口洞察里没有找到： APIH-TOKEN-TST-账号api_myai_app-KPI-tracking
    :return:
    """
    logging.basicConfig(level=logging.INFO)
    client = ApiHubTokenGetter(token_url='https://apihub-test.lenovo.com/token',
                               api_key='B88WeYP6EPIl96JFMRsV762TKFrQ5C2C',
                               username='api_myhub_backend',
                               password='w=CklROu$c')
    token_json = await client.get_api_token_async()
    await client.close()
    return token_json


def sync_get_api_hub_token_for_kmverse() -> Dict[str, Any]:
    return asyncio.run(async_get_api_hub_token_for_kmverse())

def sync_get_api_hub_token_for_myai() -> Dict[str, Any]:
    return asyncio.run(async_get_api_hub_token_for_myai())


if __name__ == "__main__":
   a = asyncio.run(async_get_api_hub_token_for_myhubbackend())
   print(a)

