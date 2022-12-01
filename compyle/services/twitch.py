# pylint: disable=unused-argument, unnecessary-lambda-assignment

import datetime
from os import getenv
from typing import Any

from requests import HTTPError

from compyle.services.routing import Endpoint, Routable


class TwitchApi(Routable):
    def __init__(self):
        helix_url = "https://api.twitch.tv/helix"
        oauth2_url = "https://id.twitch.tv/oauth2"

        # TODO https://dev.twitch.tv/docs/api/guide healthz + chaque endpoint

        self.router.register("auth", Endpoint(oauth2_url, "/token", req=["client_id", "client_secret", "grant_type"]))
        self.router.register("validate", Endpoint(oauth2_url, "/validate"))

        self.router.register("games", Endpoint(helix_url, "/games/top", opt=["after", "before", "first"]))
        self.router.register("game", Endpoint(helix_url, "/games", req=["name"]))
        self.router.register(
            "clips",
            Endpoint(helix_url, "/clips", req=["game_id"], opt=["started_at", "ended_at", "before", "first", "after"]),
        )

        self.client_id = getenv("TWITCH_APP_CLIENT_ID")
        self.client_secret = getenv("TWITCH_APP_CLIENT_SECRET")
        self.access_token = self.get_new_access_token()["access_token"]

    def __request_header(self, *, client_id=True, acces_token=True):
        header = {
            "Accept": "application/vnd.twitchtv.v5+json",
        }

        if client_id:
            header["Client-ID"] = self.client_id

        if acces_token and self.access_token:
            header["Authorization"] = f"Bearer {self.access_token}"

        return header

    def get_new_access_token(self) -> Any:
        """Gets a new client access token from Twitch API.

        Example:
            >>> self.get_new_access_token()
            >>> {'access_token': 'cfabdegwdoklmawdzdo98xt2fo512y', 'expires_in': 3600, 'token_type': 'bearer'}

        Returns:
            Any: the response deserialized as JSON if the request was successful, raises an error otherwise.
        """
        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/vnd.twitchtv.v5+json"}
        params = {"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"}

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
        try:
            self.router.request("GET", "validate", {"Authorization": f"OAuth {access_token}"})
        except HTTPError:
            return False
        return True

    def get_top_games(self, *, limit=10) -> Any:
        """Gets the top viewed categories/games on Twitch.

        Example:
            >>> self.get_top_games(limit=1)
            >>> {{"id": "33214", "name": "Fortnite", "box_art_url": "...", ...}}

        Args:
            limit (int, optional): the size of a page. Defaults to 10.

        Returns:
            Any: the list of top viewed games, raises an error otherwise.
        """
        params = {"first": max(1, min(limit, 100))}

        return self.router.request("GET", "games", self.__request_header(), **params)

    def get_game_id(self, game_name):
        params = {"name": game_name}

        response = self.router.request("GET", "game", self.__request_header(), **params)

        return response["data"][0]["id"]

    def get_game_clips(self, game_id, *, limit=100, period=3) -> Any:
        started_at = datetime.datetime.utcnow() - datetime.timedelta(days=period)
        ended_at = datetime.datetime.utcnow()

        header = self.__request_header()
        params = {
            "game_id": game_id,
            "first": max(1, min(limit, 100)),
            "started_at": started_at.isoformat("T") + "Z",
            "ended_at": ended_at.isoformat("T") + "Z",
        }

        response = self.router.request("GET", "clips", header, **params)

        _filter = lambda clip: clip["language"] == "fr" and clip["duration"] < 40
        result = list(filter(_filter, response["data"]))
        page = 0

        minimum_views = 50
        maximum_page = 10
        minimum_clips = 20

        while response["data"] and response["pagination"] and page < maximum_page:
            if response["data"][0]["view_count"] < minimum_views or len(result) > minimum_clips:
                break

            params["after"] = response["pagination"]["cursor"]
            page += 1

            response = self.router.request("GET", "clips", header, **params)

            # TODO pas du même moment

            result += list(filter(_filter, response["data"]))

        result.sort(key=lambda clip: (clip["view_count"], clip["created_at"]), reverse=True)

        # TODO duration moyenne, meilleur vue, whitelist

        return result

    def get_clip_url(self, clip: Any) -> str:
        """Gets the URL of the specified clip.

        Args:
            clip (Any): the JSON object representing the clip.

        Returns:
            str: the URL of the clip.
        """
        thumbnai_url: str = clip["thumbnail_url"]
        index = thumbnai_url.index("-preview-")

        return thumbnai_url[:index] + ".mp4"
