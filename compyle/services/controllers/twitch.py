import datetime
from typing import Any, Dict, List, Optional

from requests import HTTPError

from compyle.services.controllers.routing import Routable
from compyle.settings import TWITCH_CONFIG
from compyle.utils.descriptors import deserialize
from compyle.utils.types import Singleton

APP_ROUTES: str = "compyle/services/controllers/routes/twitch.json"


class TwitchAPI(Routable):
    """This class implements the Twitch API legacy client v5 and OAuth 2.0 for authentication.

    See:
        https://dev.twitch.tv/docs/api/reference for more information.
        https://dev.twitch.tv/docs/api/migration/ for endpoints equivalence.
    """

    __metaclass__ = Singleton

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """Initializes a new instance of the Twitch API client.

        Params:
            client_id (Optional[str]): The client id of the Twitch application. Defaults to None.
            client_secret (Optional[str]): The client secret of the Twitch application. Defaults to None.
        """
        # retrieves the routes from the JSON file
        super().__init__(deserialize(APP_ROUTES))

        # retrieves the client id and secret either from the signature parameters or from the environment variables
        self.client_id: Optional[str] = client_id or TWITCH_CONFIG.client_id
        self.client_secret: Optional[str] = client_secret or TWITCH_CONFIG.client_secret

        # checks if the client id and secret are specified
        if not self.client_id or not self.client_secret:
            raise ValueError("The client id and secret must be specified in the environment variables.")

        # generates a new client access token
        self.access_token: str = self.get_new_access_token()

    def __request_header(self, /, client_id: bool = True, acces_token: bool = True, **args) -> Dict[str, str]:
        """Constructs and returns the request header.

        Args:
            client_id (bool, optional): appends the client id if `True`. Defaults to `True`.
            acces_token (bool, optional): appends the access token if `True`. Defaults to `True`.
            **args: the additional header attributes.

        Returns:
            Dict[str, str]: the common request header with the specified attributes.
        """
        header = {"Accept": "application/vnd.twitchtv.v5+json", **args}

        if client_id and self.client_id:
            header["Client-ID"] = self.client_id

        if acces_token and self.access_token:
            header["Authorization"] = f"Bearer {self.access_token}"

        return header

    def get_new_access_token(self) -> Any:
        """Gets a new client access token from Twitch API following the Client Credentials Grant Flow.

        See:
            https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#getting-oauth-access-tokens
            https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow

        Example:
            >>> self.get_new_access_token()
            >>> {'access_token': 'cfabdegwdoklmawdzdo98xt2fo512y', 'expires_in': 3600, 'token_type': 'bearer'}

        Returns:
            Any: the response deserialized as JSON if the request was successful, raises an error otherwise.
        """
        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/vnd.twitchtv.v5+json"}
        params = {"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"}

        return self.router.request("POST", "auth", header, **params)["access_token"]

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

        See:
            https://dev.twitch.tv/docs/api/reference/#get-top-games

        Example:
            >>> self.get_top_games(limit=1)
            >>> {{"id": "33214", "name": "Fortnite", "box_art_url": "...", ...}}

        Args:
            limit (int, optional): the size of a page. Defaults to 10.

        Returns:
            Any: the list of top viewed games, raises an error otherwise.
        """
        header = self.__request_header()
        params = {"first": str(max(1, min(limit, 100)))}

        return self.router.request("GET", "games", header, **params)

    def get_game_id(self, game_name: str) -> str:
        """Returns the game id from its name.

        See:
            :func:`get_game` for related information.

        Example:
            >>> game_name = "VALORANT"
            >>> self.get_game_id(game_name)
            >>> "516575"

        Args:
            game_name (str): the name of the game to search for.

        Returns:
            str: the id of the game if the response was a success.
        """
        return self.get_game(game_name)["id"]

    def get_game(self, game_name: str) -> Any:
        """Gets the information about the game with the specified name.

        See:
            https://dev.twitch.tv/docs/api/reference/#get-games

        Example:
            >>> game_name = "VALORANT"
            >>> self.get_game_id(game_name)
            >>> {"id": "516575", "name": "VALORANT", "box_art_url": "...", ...}

        Args:
            game_name (str): the name of the game to search for.

        Returns:
            Any: the information about the game if the response was a success.
        """
        header = self.__request_header()
        params = {"name": game_name}

        response = self.router.request("GET", "game", header, **params)
        result = response["data"][0]

        if result["igdb_id"] != "":
            result["igdb_url"] = f"https://www.igdb.com/g/{result['igdb_id']}"

        return result

    def get_game_clips(self, game_id: str, *, limit=100, period=3) -> List[Any]:
        """Returns the top clips for the specified game.

        See:
            https://dev.twitch.tv/docs/api/reference/#get-clips

        Args:
            game_id (str): the id of the game.
            limit (int, optional): the maximum number of clips per page. Defaults to 100.
            period (int, optional): the date delta in days. Defaults to 3 days.

        Returns:
            List[Any]: the list of clips if the response was a success.
        """
        # date format is RFC3339 like yyyy-MM-ddTHH:mm:ssZ
        started_at = datetime.datetime.utcnow() - datetime.timedelta(days=max(1, period))
        ended_at = datetime.datetime.utcnow()

        header = self.__request_header()
        params = {
            "game_id": game_id,
            "first": str(max(1, min(limit, 100))),
            "started_at": started_at.isoformat("T") + "Z",
            "ended_at": ended_at.isoformat("T") + "Z",
        }

        return self.__parse_clips(header, params)

    def __parse_clips(self, header: Dict[str, str], params: Dict[str, Any], *, pages: int = 10) -> List[Any]:
        """Collects and normalizes the clips from the paginated request.

        Args:
            header (Dict[str, str]): the request header.
            params (Dict[str, Any]): the request parameters.
            pages (int, optional): the maximum number of pages to request.

        Returns:
            List[Any]: the list of clips.
        """
        # TODO put in signature, in **kwargs or .env ?
        min_views = 50  # the minimum number view count for a clip
        max_clips = 20  # the maximum number of clips to return
        min_duration = 5  # the minimum duration of the clips in seconds
        max_duration = 40  # the maximum duration of the clips in seconds
        language = "fr"  # the clip language in ISO-639-1 format as 2 digits code
        whitelist = []  # the list of broadcaster ids whose clips are included regardless of the other criteria
        blacklist = []  # the list of broadcaster ids whose clips are ignored

        clips = []
        for _ in range(max(1, pages)):
            response = self.router.request("GET", "clips", header, **params)

            if not response["data"] or not response["pagination"]["cursor"]:
                break

            # parses the clips and filters them with the specified criteria
            for clip in response["data"]:
                # skips the clip if the broadcaster is in the blacklist
                if clip["broadcaster_id"] in blacklist:
                    continue

                # stops the parsing if the clips have too low view_count of clips is reached
                if clip["view_count"] < min_views:
                    break

                if (
                    # checks if the broadcaster is in the whitelist
                    clip["broadcaster_id"] in whitelist
                    # checks if the video is available
                    or clip["video_id"] != ""
                    and clip["vod_offset"] is not None
                    # checks if the clip language is the specified one, if any specified all languages are valid
                    and (not language or clip["language"] == language)
                    # checks if the clip duration is between the specified bounds
                    and round(min_duration, 1) <= clip["duration"] < round(max_duration, 1)
                ):
                    # checks if the video the clip is from is not already in the list from the vod_offset
                    if not any(
                        clip["video_id"] == c["video_id"]
                        and abs(clip["vod_offset"] - c["vod_offset"]) <= max(clip["duration"], c["duration"])
                        for c in clips
                    ):
                        # adds new attributes to the clip
                        clip["clip_url"] = self.get_clip_url(clip)
                        clip["broadcaster_url"] = self.get_broadcaster_url(clip["broadcaster_name"])

                        # appends the clip to the list of clips
                        clips.append(clip)

                        # stops the parsing if enough clips were found
                        if max_clips and len(clips) == max_clips:
                            break

            params["after"] = response["pagination"]["cursor"]

        # sorts the clips by view count and creation date
        clips.sort(key=lambda clip: (clip["view_count"], clip["created_at"]), reverse=True)

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

        See:
            https://dev.twitch.tv/docs/api/reference/#get-clips

        Examples:
            >>> clip_id = "AwsomeClip"
            >>> self.get_clip(clip_id)
            >>> {"id": "AwsomeClip", "url": "https://clips.twitch.tv/AwsomeClip", "embed_url": "...", ...}

        Args:
            clip_id (str): the id of the clip to get.

        Returns:
            Any: the specified clip if the request was a success.
        """
        header = self.__request_header()
        params = {"id": clip_id}

        return self.router.request("GET", "clip", header, **params)["data"][0]

    def get_broadcaster_url(self, broadcaster_name: str) -> str:
        """Returns the URL of the specified broadcaster.

        Args:
            broadcaster_name (str): the name of the broadcaster.

        Returns:
            str: the URL of the broadcaster.
        """
        return f"https://www.twitch.tv/{broadcaster_name}"
