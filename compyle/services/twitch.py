# pylint: disable=unused-argument, unnecessary-lambda-assignment

import datetime
import logging
from os import getenv
from typing import Any

from requests import HTTPError

from compyle.services.routing import Routable


class TwitchApi(Routable):
    def __init__(self):
        helix_url = "https://api.twitch.tv/helix"
        oauth2_url = "https://id.twitch.tv/oauth2"

        routes = {
            "auth": {
                "base_url": oauth2_url,
                "slug": "/token",
                "req": ["client_id", "client_secret", "grant_type"],
            },
            "validate": {
                "base_url": oauth2_url,
                "slug": "/validate",
            },
            "games": {
                "base_url": helix_url,
                "slug": "/games",
                "opt": ["after", "before", "first"],
            },
            "game": {
                "base_url": helix_url,
                "slug": "/games",
                "req": ["name"],
            },
            "clips": {
                "base_url": helix_url,
                "slug": "/clips",
                "req": ["game_id"],
                "opt": ["started_at", "ended_at", "before", "first", "after"],
            },
            "clip": {
                "base_url": helix_url,
                "slug": "/clips",
                "req": ["id"],
            },
        }

        super().__init__(routes)

        self.client_id = getenv("TWITCH_APP_CLIENT_ID")
        self.client_secret = getenv("TWITCH_APP_CLIENT_SECRET")
        self.access_token = self.get_new_access_token()["access_token"]

    def __request_header(self, *, client_id=True, acces_token=True) -> dict:
        """Returns the request header.

        Args:
            client_id (bool, optional): Append the client id if True. Defaults to True.
            acces_token (bool, optional): Append the access token if True. Defaults to True.

        Returns:
            dict: the common request header with the specified attributes.
        """
        header = {
            "Accept": "application/vnd.twitchtv.v5+json",
        }

        if client_id and self.client_id:
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
        header = self.__request_header()
        params = {"first": max(1, min(limit, 100))}

        return self.router.request("GET", "games", header, **params)

    def get_game_id(self, game_name: str) -> str:
        """Returns the game with the specified id by name.

        Example:
            >>> game_name = "VALORANT"
            >>> self.get_game_id(game_name)
            >>> "516575"

        Args:
            game_name (str): the name of the game to get.

        Returns:
            str: the id of the game if the response was a success.
        """
        header = self.__request_header()
        params = {"name": game_name}

        response = self.router.request("GET", "game", header, **params)

        return response["data"][0]["id"]

    def get_game_clips(self, game_id: str, *, limit=100, period=3) -> Any:
        """Returns the top clips for the specified game.

        Args:
            game_id (str): the id of the game.
            limit (int, optional): the maximum number of clips per page. Defaults to 100.
            period (int, optional): the date delta in days. Defaults to 3 days.

        Returns:
            Any: the list of clips.
        """
        # date format is RFC3339 like yyyy-MM-ddTHH:mm:ssZ
        # language format is ISO-639-1 2 digits language code

        started_at = datetime.datetime.utcnow() - datetime.timedelta(days=max(1, period))
        ended_at = datetime.datetime.utcnow()

        header = self.__request_header()
        params = {
            "game_id": game_id,
            "first": max(1, min(limit, 100)),
            "started_at": started_at.isoformat("T") + "Z",
            "ended_at": ended_at.isoformat("T") + "Z",
        }

        # todo put in signature
        minimum_views = 50
        maximum_page = 10
        minimum_clips = 20
        language = "fr"

        logger = logging.getLogger(__name__)

        clips = []
        for page in range(maximum_page):
            response = self.router.request("GET", "clips", header, **params)

            if response["data"]:
                for clip in response["data"]:
                    if (
                        clip["video_id"] != ""
                        and clip["vod_offset"] is not None
                        and clip["language"] == "fr"
                        and clip["duration"] < 40
                    ):
                        if not any(
                            clip["video_id"] == selected["video_id"]
                            and abs(clip["vod_offset"] - selected["vod_offset"])
                            <= max(clip["duration"], selected["duration"])
                            for selected in clips
                        ):
                            clips.append(clip)

                if len(clips) >= minimum_clips:
                    logger.debug("Parsing stopped, enough clips were found (%s)", len(clips))
                    break

                if response["data"][0]["view_count"] < minimum_views:
                    logger.debug("Parsing stopped, maximum view count for this page is too low (>= %s)", minimum_views)
                    break

                if not response["pagination"]["cursor"]:
                    logger.debug("Parsing stopped, there is no more pages")
                    break

                params["after"] = response["pagination"]["cursor"]

        clips.sort(key=lambda clip: (clip["view_count"], clip["created_at"]), reverse=True)
        logger.debug(
            "Parsing done, %s/~%s of the clips kept in the %d last days",
            len(clips),
            page * limit,
            max(1, period),
        )

        # TODO duration moyenne, meilleur vue, whitelist

        return clips

    def get_clip_url(self, clip: Any) -> str:
        """Gets the URL of the specified clip.

        Examples:
            >>> game_id = "516575"
            >>> clips = self.get_game_clips(game_id)
            >>> self.get_clip_url(clips[0])
            >>> "https://clips-media-assets2.twitch.tv/vp0-ZEvQSIpEfV5tDDscTw/vod-1669323688-offset-22038.mp4"

        Args:
            clip (Any): the JSON object representing the clip.

        Returns:
            str: the URL of the clip.
        """
        thumbnai_url: str = clip["thumbnail_url"]
        index = thumbnai_url.index("-preview-")

        return thumbnai_url[:index] + ".mp4"

    def get_clip(self, clip_id: str) -> Any:
        """Returns the clip with the specified id.

        Args:
            clip_id (str): the id of the clip to get.

        Returns:
            Any: the specified clip if the request was a success
        """
        header = self.__request_header()
        params = {"id": clip_id}

        return self.router.request("GET", "clip", header, **params)["data"][0]
