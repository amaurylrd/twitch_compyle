# pylint: disable=unused-argument

from os import getenv
from typing import Any
import datetime
from requests import HTTPError
from routing import Endpoint, Routable


class TwitchApi(Routable):
    def __init__(self):
        helix_url = "https://api.twitch.tv/helix"
        oauth2_url = "https://id.twitch.tv/oauth2"

        self.router.register("auth", Endpoint(oauth2_url, "/token", req=["client_id", "client_secret", "grant_type"]))
        self.router.register("validate", Endpoint(helix_url, "/validate"))
        self.router.register("games", Endpoint(helix_url, "/games/top", opt=["after", "before", "first"]))
        self.router.register(
            "clips",
            Endpoint(helix_url, "/clips", req=["game_id"], opt=["started_at", "ended_at", "before", "first", "after"]),
        )

        self.client_id = getenv("TWITCH_APP_CLIENT_ID")
        self.client_secret = getenv("TWITCH_APP_CLIENT_SECRET")
        self.access_token = self.get_new_access_token()

    def get_new_access_token(self) -> Any:
        """Gets a new client access token from Twitch API.

        Example:
            >>> self.get_new_access_token()
            >>> {'access_token': 'cfabdegwdoklmawdzdo98xt2fo512y', 'expires_in': 3600, 'token_type': 'bearer'}

        Returns:
            Any: the response deserialized as JSON if the request was successful, raises an error otherwise.
        """
        params = {"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"}
        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/vnd.twitchtv.v5+json"}

        return self.router.request("POST", "auth", header, **params)

    def is_access_token_valid(self, access_token: str) -> bool:
        """Checks if the specified access token is valid.

        See:
            https://dev.twitch.tv/docs/authentication/validate-tokens

        Args:
            access_token (str): the client access token.

        Returns:
            bool: `True` if the token is valid, `False` otherwise.
        """
        header = {"Authorization": f"OAuth {access_token}"}

        try:
            self.router.request("GET", "validate", header)
        except HTTPError:
            return False
        return True

    def get_top_games(self, *, limit=10) -> Any:
        """Gets the top viewed categories/games on Twitch.

        Example:
            >>> self.get_top_games(limit=1)
            >>> [{"id": "33214", "name": "Fortnite", "box_art_url": "..."}]

        Args:
            limit (int, optional): the size of a page. Defaults to 10.

        Returns:
            Any: the list of top viewed games, raises an error otherwise.
        """
        params = {"first": limit}
        header = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}

        return self.router.request("GET", "games", header, **params)

    def get_games_clips(self, game_id, *, limit=100, period=7) -> Any:
        started_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=period)
        ended_at = datetime.datetime.now(datetime.timezone.utc)

        params = {
            "game_id": game_id,
            "first": limit,
            "started_at": started_at.astimezone().isoformat(),
            "ended_at": ended_at.astimezone().isoformat(),
        }
        headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }

        response = self.router.request("GET", "clips", headers, **params)
        result = response["data"]

        while response["data"] and response["pagination"]:
            params["after"] = response["pagination"]["cursor"]
            response = self.router.request("GET", "clips", headers, **params)
            result += response["data"]

        return result


from compyle.preloader import launch_after_preload


def test():
    api = TwitchApi()
    # print("test1", api.get_new_access_token())
    print("test", api.get_top_games())


launch_after_preload(test)

# if "data" in serialized:
#                 result: list = serialized["data"]

#                 while serialized["data"] and serialized["pagination"] is not None:
#                     kwargs["after"] = serialized["pagination"]["cursor"]

#                     url: str = router.route(namespace, *args, **kwargs)
#                     response: Response = HttpMethod[method](url, headers=header, timeout=None)

#                     serialized = response.json()
#                     result.extend(serialized["data"])
