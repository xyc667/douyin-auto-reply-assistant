import base64
import json

from dy_apis.douyin_api import DouyinAPI
from utils.dy_util import trans_cookies, generate_msToken


def _parse_sdk_payload(raw: str) -> dict:
    """Parse WEB_PROTECT / KEYS values stored in .env."""
    if not raw:
        return {}

    outer = json.loads(raw)
    data = outer.get('data', '')
    if isinstance(data, dict):
        return data
    if not isinstance(data, str) or not data:
        return {}

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        # dotenv may turn escaped \n into real newlines inside JSON strings.
        repaired = data.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
        return json.loads(repaired)


class DouyinAuth:
    def __init__(self):
        self.cookie = None
        self.cookie_str = None
        self.private_key = None
        self.ticket = None
        self.ts_sign = None
        self.client_cert = None
        self.ree_public_key = None
        self.uid = None
        self.msToken = None

    def perepare_auth(self, cookieStr: str, web_protect_: str = "", keys_: str = ""):
        self.cookie = trans_cookies(cookieStr)
        self.cookie_str = cookieStr
        self.msToken = self.cookie["msToken"] if "msToken" in self.cookie else generate_msToken()
        self.cookie["msToken"] = self.msToken
        self.cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookie.items()])
        if web_protect_ != "":
            web_protect_ = _parse_sdk_payload(web_protect_)
            self.ticket = web_protect_['ticket']
            self.ts_sign = web_protect_['ts_sign']
            self.client_cert = web_protect_['client_cert']
        if keys_ != "":
            keys_ = _parse_sdk_payload(keys_)
            self.private_key = keys_['ec_privateKey']
            self.ree_public_key = base64.b64encode(self.private_key.encode()).decode()


    def get_uid(self):
        if self.uid is None:
            self.uid = DouyinAPI.get_my_uid(self)
        return self.uid
