import json

from requests.cookies import cookiejar_from_dict, RequestsCookieJar
from requests.structures import CaseInsensitiveDict


class AbstractFakeResp(object):
    text: str
    status_code = 200
    headers: CaseInsensitiveDict
    cookies: RequestsCookieJar

    def __init__(self, *args, **kwargs):
        self.headers = CaseInsensitiveDict()
        self.cookies = cookiejar_from_dict({})

    @property
    def content(self) -> bytes:
        return self.text.encode("utf-8")

    def json(self) -> dict:
        return json.loads(self.text)
