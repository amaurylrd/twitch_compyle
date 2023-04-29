from os import getenv
from typing import Dict, List, Tuple
from compyle.services.routing import Routable
from compyle.utils.enums import Enum


class PrivacyStatus(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


routes = {
    "auth": {
        "base_url": "https://accounts.google.com/o/oauth2/",
        "slug": "token",
        "req": ["client_id", "client_secret"],
    },
    "categories": {
        "base_url": "https://www.googleapis.com/youtube/v3/",
        "slug": "videoCategories",
        "req": ["part"],
        "opt": ["id", "regionCode"],
    },
    "upload": {
        "base_url": "https://www.googleapis.com/upload/youtube/v3",
        "slug": "videos",
    },
}


class YoutubeApi(Routable):
    """This class implements the Youtube data API v3 and OAuth 2.0 for authentication."""

    def __init__(self):
        """Initializes a new instance of the Youtube API client."""
        # retrieves the routes description from the JSON file
        super().__init__(routes)

        # retrieves the client id and secret from the environment variables
        self.client_id: str = getenv("YOUTUBE_APP_CLIENT_ID")
        self.client_secret: str = getenv("YOUTUBE_APP_CLIENT_SECRET")

        # generates a new client access token
        self.access_token: str = ""

    # TODO https://developers.google.com/identity/protocols/oauth2?hl=fr

    def __request_header(self, *, acces_token: bool = True, **args) -> Dict[str, str]:
        """Constructs and returns the request header.

        Args:
            acces_token (bool, optional): appends the access token if `True`. Defaults to `True`.
            **args: the additional header attributes.

        Returns:
            Dict[str, str]: the common request header with the specified attributes.
        """
        header = {"Accept": "application/json", **args}

        if acces_token and self.access_token:
            header["Authorization"] = f"Bearer {self.access_token}"

        return header

    #     curl \
    #   'https://youtube.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode=FR&key=[YOUR_API_KEY]' \
    #   --header 'Authorization: Bearer [YOUR_ACCESS_TOKEN]' \
    #   --header 'Accept: application/json' \
    #   --compressed

    def get_categories(self, region_code: str = "FR") -> List[Tuple[str, int]]:
        """Retrieves the list of categories in the region specified by the region_code in the format ISO 3166-1 alpha-2.

        Example:
            >>> self.get_categories("FR")
            >>> [("Film & Animation", 2), ("Music", 10), ...]

        Args:
            region_code (str, optional): the code of the region. Defaults to "FR".

        Returns:
            List[Tuple[str, int]]: the list of assignable categories in the specified region.
        """
        header = self.__request_header()
        params = {"part": "snippet", "regionCode": region_code}

        response = self.router.request("GET", "categories", header, **params)
        categories = [
            (item["snipper"]["title"], item["id"]) for item in response["items"] if item["snippet"]["assignable"]
        ]

        return categories

    def is_category(self, category: int = 22) -> bool:
        header = {}
        params = {"part": "snippet", "id": category}

        try:
            self.router.request("GET", "categories", header, **params)
        except Exception as error:
            print(error)
            return False

        return True

    def upload_video(self, filename, title, description, tags, category):
        # 256 Go
        # Types MIME de médias acceptés : video/*, application/octet-stream

        body = {
            "snippet": {"title": title, "description": description, "tags": tags, "categoryId": category},
            "status": {"privacyStatus": PrivacyStatus.PRIVATE},
        }

        # part = snippet,status
        # notifySubscribers = True


youtube_api = YoutubeApi()
print(youtube_api.router.get_registered())
