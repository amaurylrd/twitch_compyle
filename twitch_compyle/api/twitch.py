import os
import os.path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple
)

import requests
from rest_framework import status

from tokenizer import deserialize_token, serialize_token

OAUTH2_URL = "https://id.twitch.tv/oauth2"
OAUTH2_TOKEN = "./twitch.json"

HELIX_URL = "https://api.twitch.tv/helix"

CLIENT_ID = os.getenv("TWITCH_APP_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_APP_CLIENT_SECRET")


def get_new_access_token() -> Optional[Dict[str, Any]]:
    """Gets a new client access token from Twitch API.

    Example:
        >>> get_new_access_token()
        >>> {'access_token': 'cfabdegwdoklmawdzdo98xt2fo512y', 'expires_in': 3600, 'token_type': 'bearer'}
    
    Returns:
        Optional[Dict[str, Any]]: the response deserialized as JSON if the request was successful, `None` otherwise.
    """
    SLUG = "/token"
    REQUIRED_PARAMS = ["client_id", "client_secret", "grant_type"]

    url = OAUTH2_URL + SLUG
    params = dict(zip(REQUIRED_PARAMS, [CLIENT_ID, CLIENT_SECRET, "client_credentials"]))
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/vnd.twitchtv.v5+json"}
    response = requests.post(url, params=params, headers=headers)

    return response.json() if response.status_code == status.HTTP_200_OK else None


def is_access_token_valid(access_token: Dict[str, Any]) -> bool:
    """Checks if the specified access token is valid.

    See:
        https://dev.twitch.tv/docs/authentication/validate-tokens

    Args:
        access_token (Dict[str, Any]): the access token to be checked.
        
    Returns:
        bool: `True` if the token is valid, `False` otherwise.
    """
    SLUG = "/validate"

    url = OAUTH2_URL + SLUG
    header = {"Authorization": f"OAuth {access_token}"}
    response = requests.get(url, headers=header)

    return response.status_code == status.HTTP_200_OK


def refresh_access_token() -> str:
    """Refreshes the access token if it is expired.
        
    See:
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth
        
    Returns:
        str: the client access token or raises an exception if the operation failed.
    """
    if os.path.exists(OAUTH2_TOKEN):
        json = deserialize_token(OAUTH2_TOKEN)

        if "access_token" in json and is_access_token_valid(json["access_token"]):
            return json["access_token"]
    
        os.remove(OAUTH2_TOKEN)
    
    if json := get_new_access_token():
        serialize_token(OAUTH2_TOKEN, json)
    
        return json["access_token"]

    raise RuntimeError("Failed to load or refresh the client access token")


CLIENT_ACCESS_TOKEN = refresh_access_token()


def get_top_games(*, limit: int = 10) -> Optional[List[Tuple[str, str]]]:
        """Gets the top viewed games on Twitch.

        Example:
            >>> get_top_games("cfabdegwdoklmawdzdo98xt2fo512y", limit=2)
            >>> [('509658', 'Just Chatting'), ('32982', 'Grand Theft Auto V')]
        
        Args:
            limit (int, optional): the size of the lader. Defaults to 10.

        Returns:
            List[Tuple]: the list of top viewed games information on Twitch.
        """
        SLUG = "/games/top"
        
        url = HELIX_URL + SLUG
        params = {"first": limit}
        headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {CLIENT_ACCESS_TOKEN}"}
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == status.HTTP_200_OK:
            return [(game['id'], game['name']) for game in response.json()["data"]] # TODO mieux filter
        
def get_games_clips(game_id, *, limit: int = 10, started_at, iso_language: str = "FR") -> Optional[List[Tuple]]:
    SLUG = "/clips"
    
    url = HELIX_URL + SLUG
    params = {"game_id": game_id, "first": limit} # started_at
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {CLIENT_ACCESS_TOKEN}"}
    response = requests.get(url, params=params, headers=headers)

    return response
# todo language broadcaster_language data[].language
# broadcaster_name

# data[0].url
