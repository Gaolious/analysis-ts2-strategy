from typing import Dict, Union

import requests

REQUEST_TIMEOUT = 10

LOGGING_MENU = 'core.requests_helper'

import urllib3
urllib3.disable_warnings()


class CrawlingHelper(object):

    @classmethod
    def _request(cls, method: str, url: str, headers: Dict, payload: Dict, params: Dict, cookies: Dict,
                 timeout=REQUEST_TIMEOUT, **kwargs) -> requests.Response:
        """
        url에 대해 request

        Args:
            url:
            headers:
            payload:

        Returns:
            resp
        """
        with requests.Session() as s:
            s.headers = headers
            method = method.lower()
            caller = getattr(s, method)
            resp = caller(
                url=url,
                data=payload,
                headers=headers,
                timeout=timeout,
                cookies=cookies or {},
                params=params or {},
                verify=False,
            )
            if resp and resp.status_code >= 400:
                raise Exception(f'Invalid status code : {resp.status_code}')

            return resp

    @classmethod
    def get(cls, *, url: str, headers: Dict, payload: Dict, params=None, cookies: Dict = None,
            **kwargs) -> requests.Response:
        return cls._request(method='get', url=url, headers=headers, payload=payload, params=params, cookies=cookies,
                            **kwargs)

    @classmethod
    def post(cls, *, url: str, headers: Dict, payload: Union[str, Dict], params=None, cookies: Dict = None,
             **kwargs) -> requests.Response:
        return cls._request(method='post', url=url, headers=headers, payload=payload, params=params, cookies=cookies,
                            **kwargs)
