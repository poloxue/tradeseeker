import requests
from pyotp import TOTP

from cli.apis.constant import TRADEAPI_HOST


def endpoint(path):
    return f"{TRADEAPI_HOST}/{path}"


class AuthAPI:
    def __init__(self):
        self.access_token = ""

    def login(self, username, password, google2fa_secret):
        google2fa = TOTP(google2fa_secret).now()
        data = {"username": username, "password": password, "google2fa": google2fa}
        r = requests.post(endpoint("token"), data=data)
        self.access_token = r.json()["access_token"]

    def get(self, url, params=None):
        return self.request("get", url=url, params=params)

    def post(self, url, data=None):
        return self.request("post", url=url, data=data)

    def request(self, method, url, params=None, data=None):
        # access_token = login("poloxue", "NineTTE4mxE6")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.request(method, url, headers=headers, json=data, params=params)
        return r.json()
