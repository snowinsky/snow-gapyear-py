# pip install requests requests-toolbelt tenacity or json(可选加速序列化)
import logging
import ssl
from typing import Dict, Any, Optional, Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lenovo.apihub.ApiHubTokenGetter import sync_get_api_hub_token_for_kmverse

_log = logging.getLogger(__name__)

# ------------------全局常量------------------
CONN_TIMEOUT = 5  # TCP建连超时(s)
READ_TIMEOUT = 20  # socket读超时(s)
MAX_RETRIES = Retry(
    total=1,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504])
POOL_SIZE = 100  # pool_connections/pool_maxsize


class SyncKMVerseSdk:
    """
    requests-based、线程安全的 HTTP Client。
    """

    def __init__(self,
                 base_url: str,
                 api_key: str,
                 km_verse_key: str,
                 token_client):
        """
        :param base_url:       apihubPrcKmApiUrl（不含尾斜杠）
        :param api_key:         X-API-KEY header值
        :param km_verse_key:   km-verse-key header值
        :param token_client:   sync callable -> dict{"access_token":"..."}
                               demo可用之前实现的 TokenClient().get_api_token()
                               （同步版本）
                               """

        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.km_verse_key = km_verse_key
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
        url = f"{self.base_url}/tpass/kmverse/outerapi/v1{url_no_params}"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-API-KEY": self.api_key,
            "km-verse-key": self.km_verse_key,
            "Authorization": f"Bearer {self._fresh_access_token()}",
        }

        _log.info("%s  %s", method.upper(), url)

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

    def api47_updateDocTag(self, doc_id: str, tag: str) -> str:
        return self.send_request('/document/tag', None, 'PUT', {"docId": doc_id, "tag": tag})

    def api64_getDocByKbId(self, knowledgeBaseId, page, rows, keyword, parentDocId) -> str:
        params = {'page': page,
                  'rows': rows,
                  'keyword': keyword,
                  'parentDocId': parentDocId}
        return self.send_request(f'/knowledgeBase/{knowledgeBaseId}/documents', params, 'GET')

    def api65_updateKb(self, knowledgeBaseId, owner, knowledgeBase, description) -> str:
        body = {
            'owner': owner,
            'knowledgeBase': knowledgeBase,
            'description': description
        }
        return self.send_request(f'/knowledgeBase/{knowledgeBaseId}/updateKnowledgeBaseInfo', 'PUT', body)

    def api70_getFolderByKbId(self, knowledgeBaseId) -> str:
        return self.send_request(f'/folder/{knowledgeBaseId}/getFolder', 'GET')

    def api79_getCreatedKbListByItCode(self, itCode, page, rows, keyword) -> str:
        params = {
            'itCode': itCode,
            'page': page,
            'rows': rows,
            'keyword': keyword
        }
        return self.send_request(f'/knowledgeBase/{projectId}/userKnowledgeBases', params, 'GET')

    def api80_hasPermissionOfKbId(self, knowledgeBaseId, itcode) -> str:
        params = {
            'itCode': itcode
        }
        return self.send_request(f'/knowledgeBase/{knowledgeBaseId}/hasPermission', params, 'GET')

    def api81_getSharedKbListByItCode(self, itCode, page, rows, keyword) -> str:
        params = {
            'itCode': itCode,
            'page': page,
            'rows': rows,
            'keyword': keyword
        }
        return self.send_request(f'/knowledgeBase/{projectId}/direct/permission/knowledgeBases', params, 'GET')

    def api49_uploadFileTo(self, doc_id, tag) -> str:
        # TODO
        return self.send_request('/knowledge/upload', 'POST', {"docId": doc_id, "tag": tag})

    def api50_updateDocChunk(self, docId, chunkId, chunkText) -> str:
        body = {
            {
                "docId": docId,
                "chunkId": chunkId,
                "chunkText": chunkText,
            }
        }
        return self.send_request('/document/chunk/update', None, 'PUT', body)

    def api51_insertDocChunk(self, docId, chunkId, chunkText) -> str:
        body = {
            "docId": docId,
            "chunkId": chunkId,
            "chunkText": chunkText,
        }
        return self.send_request('/document/chunk/add', None, 'POST', body)

    def api56_deleteDocChunk(self, docId, chunkId) -> str:
        body = {
            "docId": docId,
            "chunkId": chunkId,
        }
        return self.send_request('/document/chunk/delete', None, 'DELETE', body)

    def api52_searchKbId(self, knowledgeBaseId, query) -> str:
        body = {
            "projectId": projectId,
            "relation": [
                {
                    "knowledgeBaseId": knowledgeBaseId,
                    "docIds": [

                    ],
                    "filter": "",
                    "embedding": ""
                }
            ],
            "query": query,
            "indexMode": "keyword",
            "similarityTopK": 3,
            "score": 4
        }
        return self.send_request('/knowledge/retrieval', None, 'POST', body)

    def api60_getDeleteTaskStatus(self, knowledgeId) -> str:
        return self.send_request(f'/knowledge/delete/{knowledgeId}', None, 'DELETE')

    def api57_getPageChunkByKbId(self, knowledgeId, page, pageSize) -> str:
        return self.send_request('/document/pageChunks', {
            'docId': knowledgeId,
            'page': page,
            'pageSize': pageSize
        }, 'GET')

    def api58_getUpdateTagTaskStatus(self, taskId) -> str:
        return self.send_request('/task/updateTag/status', {'taskId': taskId}, 'GET')

    def api59_getUploadFileTaskStatus(self, taskId) -> str:
        return self.send_request('/task/docChunk/status', {'taskId': taskId}, 'GET')

    def api60_getDocDeleteTaskStatus(self, taskId) -> str:
        return self.send_request('/task/docDelete/status', {'taskId': taskId}, 'GET')

    def api61_insertKb(self, kbName, kbDescription, owner) -> str:
        return self.send_request('/collection', method='POST', json_body={
            "businessUnit": "Others",
            "description": kbDescription,
            "knowledgeBase": kbName,
            "model": "bge-m3",
            "owner": owner,
            "projectId": projectId
        })

    def api66_insertFolder(self, knowledgeBaseId, folderName, parentFolderId) -> str:
        return self.send_request('/folder', method='POST', json_body={
            "knowledgeBaseId": knowledgeBaseId,
            "folderName": folderName,
            "parentFolderId": parentFolderId
        })

    def api67_deleteFolder(self, folderId) -> str:
        return self.send_request(f'/folder/{folderId}', method='DELETE')

    def api68_updateFolderName(self, knowledgeBaseId, folderId, folerName) -> str:
        return self.send_request(f'/folder/{knowledgeBaseId}/{folderId}/rename', method='PUT', json_body={
            "folderName": folerName
        })

    def api69_batchDeleteDocIds(self, docIds: []) -> str:
        return self.send_request('/document/batch', method='DELETE', json_body=docIds)

    def api71_moveDoc(self, from_docId, to_docId) -> str:
        return self.send_request('/folder/move', method='POST', json_body={
            "docId": [
                from_docId
            ],
            "parentDocId": to_docId
        })

    def api72_getKbListByItCode(self, itCode, rows, page, keyword) -> str:
        return self.send_request(f'/knowledgeBase/{projectId}/knowledgeBases', method='GET', json_params={
            'itCode': itCode,
            'rows': rows,
            'page': page,
            'keyword': keyword,
        })

    def api73_deleteKbById(self, knowledgeBaseId) -> str:
        return self.send_request(f'/knowledgeBase/{knowledgeBaseId}', method='DELETE')

    def api74_getUserListWithPermission(self, knowledgeBaseId) -> str:
        return self.send_request(f'/knowledgeBase/{knowledgeBaseId}/hasPermissionUsers', method='GET')

    def api75_addPermission(self, knowledgeBaseId, itCode, permissionType) -> str:
        return self.send_request('/knowledgeBase/permission/grant', method='POST', json_body={
            "projectId": projectId,
            "knowledgeBaseId": knowledgeBaseId,
            "username": itCode,
            "permissionType": permissionType
        })

    def api76_removePermission(self, knowledgeBaseId, itCode, permissionType) -> str:
        return self.send_request('/knowledgeBase/permission/revoke', method='POST', json_body={
            "projectId": projectId,
            "knowledgeBaseId": knowledgeBaseId,
            "username": itCode,
            "permissionType": permissionType
        })


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    client = SyncKMVerseSdk(
        base_url="https://apihub-test.lenovo.com/uat/v2/product/tpass",
        api_key="L6Mf5DHsdEl6tfKKG01PKUkYzHI2zaaH",
        km_verse_key="A+/oiGFzc8FmKV5afgXeML/R8RwXgXt9khNoAj6/ZZk=",
        token_client=lambda: sync_get_api_hub_token_for_kmverse())  # sync callable

    projectId = 520
    itcode = 'jigs2'

    try:
        body_str = client.api52_searchKbId(153247729047877, "今天心情")
        print(body_str)
    finally:
        client.close()
