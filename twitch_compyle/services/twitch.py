# pylint: disable=unused-argument

from os import getenv
from typing import Any, Dict, Optional

from request import request
from routing import Endpoint, Routable
from decorators import DecoratorError


class TwitchApi(Routable):
    def __init__(self):
        self.client_id = getenv("TWITCH_APP_CLIENT_ID")
        self.client_secret = getenv("TWITCH_APP_CLIENT_SECRET")

        helix_url = "https://api.twitch.tv/helix"
        oauth2_url = "https://id.twitch.tv/oauth2"

        self.router.register("auth", Endpoint(oauth2_url, "/token", req=["client_id", "client_secret", "grant_type"]))
        self.router.register("validate", Endpoint(helix_url, "/validate"))

    def get_access_token(self) -> Optional[Dict[str, Any]]:
        params = {"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"}
        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/vnd.twitchtv.v5+json"}

        @request("POST", "auth", **header)
        def _get_acces_token(self, response=None, **params):
            return response

        return _get_acces_token(self, **params)

    def is_access_token_valid(self, access_token: str) -> bool:
        header = {"Authorization": f"OAuth {access_token}"}

        @request("GET", "validate", **header)
        def _is_access_token_valid(self, response=None):
            return response

        try:
            _is_access_token_valid(self)
            return True
        except DecoratorError:
            return False

    def get_top_games(self, **kwargs) -> Optional[Dict[str, Any]]:
        pass


from twitch_compyle.preloader import launch_after_preload


def test():
    api = TwitchApi()
    print(api.get_access_token())


launch_after_preload(test)
