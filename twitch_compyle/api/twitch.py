import logging
import os
import os.path
from typing import Any, Dict, List, Optional, Tuple
import datetime
import requests
from rest_framework import status

from twitch_compyle.api.tokenizer import deserialize_token, serialize_token

LOGGER = logging.getLogger(__name__)

HELIX_URL = "https://api.twitch.tv/helix"

OAUTH2_URL = "https://id.twitch.tv/oauth2"
OAUTH2_TOKEN = "./twitch.json"

BEARER_TOKEN = None


class TwitchAPI:
    def __init__(self):
        self.client_id = os.getenv("TWITCH_APP_CLIENT_ID")
        self.client_secret = os.getenv("TWITCH_APP_CLIENT_SECRET")
        self.access_token = self.refresh_access_token()

    def get_new_access_token(self) -> Optional[Dict[str, Any]]:
        """Gets a new client access token from Twitch API.

        Example:
            >>> self.get_new_access_token()
            >>> {'access_token': 'cfabdegwdoklmawdzdo98xt2fo512y', 'expires_in': 3600, 'token_type': 'bearer'}

        Returns:
            Optional[Dict[str, Any]]: the response deserialized as JSON if the request was successful, `None` otherwise.
        """
        slug = "/token"
        url = OAUTH2_URL + slug

        required_params = ["client_id", "client_secret", "grant_type"]
        params = dict(zip(required_params, [self.client_id, self.client_secret, "client_credentials"]))

        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/vnd.twitchtv.v5+json"}
        response = requests.post(url, params=params, headers=headers, timeout=None)

        return response.json() if response.status_code == status.HTTP_200_OK else None

    def is_access_token_valid(self, access_token: str) -> bool:
        """Checks if the specified access token is valid.

        See:
            https://dev.twitch.tv/docs/authentication/validate-tokens

        Args:
            access_token (str): the client access token.

        Returns:
            bool: `True` if the token is valid, `False` otherwise.
        """
        slug = "/validate"
        url = OAUTH2_URL + slug

        header = {"Authorization": f"OAuth {access_token}"}
        response = requests.get(url, headers=header, timeout=None)

        return response.status_code == status.HTTP_200_OK

    def refresh_access_token(self) -> str:
        """Refreshes the access token if it is expired.

        See:
            https://dev.twitch.tv/docs/authentication/getting-tokens-oauth

        Returns:
            str: the client access token or raises an exception if the operation failed.
        """
        if os.path.exists(OAUTH2_TOKEN):
            LOGGER.debug("Loading access token from file %s", OAUTH2_TOKEN)
            json = deserialize_token(OAUTH2_TOKEN)

            if "access_token" in json and self.is_access_token_valid(json["access_token"]):
                return json["access_token"]

            LOGGER.debug("The specified token is expired, requesting a new one")
            os.remove(OAUTH2_TOKEN)

        if json := self.get_new_access_token():
            serialize_token(OAUTH2_TOKEN, json)
            return json["access_token"]

        raise RuntimeError("Failed to load or refresh the client access token")

    def get_top_games(self, *, limit: int = 10) -> Optional[List[Tuple[str, str]]]:
        """Gets the top viewed games on Twitch.

        Example:
            >>> self.get_top_games("cfabdegwdoklmawdzdo98xt2fo512y", limit=1)
            >>> [{"id": "33214", "name": "Fortnite", "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/33214-{width}x{height}.jpg"}]

        Args:
            limit (int, optional): the size of the lader. Defaults to 10.

        Returns:
            List[Tuple]: the list of top viewed games information on Twitch.
        """

        slug = "/games/top"
        url = HELIX_URL + slug

        params = {"first": limit}
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, params=params, headers=headers, timeout=None)

        if response.status_code == status.HTTP_200_OK:
            return response.json()["data"]
        # TODO mieux filter

    def get_games_clips(self, game_id, *, limit=100, **kwargs) -> Optional[List[Tuple]]:
        slug = "/clips"
        url = HELIX_URL + slug  # todo routes url method qui merge base_url and slug

        params = {
            "game_id": game_id,
            "first": limit,
            "started_at": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).isoformat(),
            "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }

        response = requests.get(url, params=params, headers=headers, timeout=None)
        response_json = response.json()  # sorted descending by views

        result = response_json["data"]

        while limit > len(response_json["data"]) and response_json["pagination"]:
            print(response_json["pagination"])
            # if response.status_code == status.HTTP_200_OK:
            #    return response.json()["data"]

            params["after"] = response_json["pagination"]["cursor"]
            response = requests.get(url, params=params, headers=headers, timeout=None)
            response_json = response.json()
            print(len(response_json["data"]))
            result += response_json["data"]

        result.sort(key=lambda x: x["view_count"], reverse=True)
        print(len(result))
        exit()
        return result

        # if clip["language"] == "fr":
        #     print(clip["url"])
        # print(clip)
        # duration
        # broadcaster_name blacklist


# todo language broadcaster_language data[].language
# broadcaster_name

# data[0].url
