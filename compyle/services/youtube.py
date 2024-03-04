import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from requests import HTTPError

from compyle.services.common import Routable
from compyle.settings import YOUTUBE_CONFIG
from compyle.utils.descriptors import deserialize
from compyle.utils.types import Enum, Singleton

APP_ROUTES: str = "compyle/services/controllers/routes/youtube.json"


class PrivacyStatus(Enum):
    """Represents the upload privacy status for a video."""

    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class Scopes(Enum):
    """Represents the scopes for the Youtube API service."""

    YOUTUBE_ACCOUNT = "https://www.googleapis.com/auth/youtube"
    CHANNEL_MEMBERSHIPS = "https://www.googleapis.com/auth/youtube.channel-memberships.creator"
    FORCE_SSL = "https://www.googleapis.com/auth/youtube.force-ssl"
    READ_ONLY = "https://www.googleapis.com/auth/youtube.readonly"
    UPLOAD_VIDEOS = "https://www.googleapis.com/auth/youtube.upload"
    YOUTUBE_PARTNER = "https://www.googleapis.com/auth/youtubepartner"
    CHANNEL_AUDIT = "https://www.googleapis.com/auth/youtubepartner-channel-audit"


class YoutubeAPI(Routable):
    """This class implements the Youtube data API v3 and OAuth 2.0 for authentication.

    See:
        https://console.cloud.google.com/apis/library/youtube.googleapis.com.
    """

    __metaclass__ = Singleton

    def __init__(
        self, client_id: Optional[str] = None, client_secret: Optional[str] = None, redirect_uri: Optional[str] = None
    ):
        """Initializes a new instance of the Youtube API client.

        Params:
            client_id (Optional[str]): The client id of the Youtube application. Defaults to None.
            client_secret (Optional[str]): The client secret of the Youtube application. Defaults to None.
            redirect_uri (Optional[str]): The redirect uri of the Youtube application. Defaults to None.
        """
        # retrieves the routes description from the JSON file
        super().__init__(deserialize(APP_ROUTES))

        # retrieves the client id and secret either from the parameters or the environment variables
        self.client_id: Optional[str] = client_id or YOUTUBE_CONFIG.client_id
        self.client_secret: Optional[str] = client_secret or YOUTUBE_CONFIG.client_secret

        # checks if the client id and secret are specified
        if not self.client_id or not self.client_secret:
            raise ValueError("The client id and secret must be specified in the environment variables.")

        # retrieves the redirect uri and client email either from the parameters or from the environment variables
        self.redirect_uri: str = redirect_uri or YOUTUBE_CONFIG.redirect_uri
        user_email_address: Optional[str] = YOUTUBE_CONFIG.client_email

        # retrieves the authorization code from authentication service
        autorization_code: str = self.authentificate(user_email_address)
        # TODO réparer ici
        code = input("Enter the authorization code: ")
        self.access_token = self.get_access_token(code)

    # pylint: disable=line-too-long
    def authentificate(self, login_hint: Optional[str] = None) -> str:
        """Redirect the user to Google's OAuth 2.0 server to initiate the authentication and authorization process.
        Google's OAuth 2.0 server authenticates the user and obtains consent from the user for your application to access the requested scopes.
        The response is sent back to your application using the redirect URL you specified.

        See:
            https://developers.google.com/identity/protocols/oauth2?hl=en#webserver for the OAuth 2.0 flow and web server applications.
            https://developers.google.com/identity/protocols/oauth2/web-server?hl=en#httprest_2 for the Authorization Code Flow.
            https://developers.google.com/identity/protocols/oauth2/scopes#youtube for scopes.

        Params:
            login_hint (Optional[str]): the email address of the user to log in. Defaults to None.

        Returns:
            str: the authorization code
        """
        params = {
            "client_id": self.client_id,
            "scope": " ".join([Scopes.READ_ONLY.value, Scopes.UPLOAD_VIDEOS.value]),  # space-delimited list
            "access_type": "offline",
            "include_granted_scopes": "true",
            "response_type": "code",
            "state": "state_parameter_passthrough_value",
            "redirect_uri": self.redirect_uri,
            "prompt": "consent",
        }

        if login_hint:
            params["login_hint"] = login_hint

        response = self.router.request("POST", "auth", {}, return_json=False, **params)
        response_uri: str = response.headers.get("Location") or response.url

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):  # pylint: disable=invalid-name
                code: str = parse_qs(urlparse(self.path).query)["code"][0]
                self.send_response(200)
                self.send_header("test", "text/html")
                self.end_headers()
                self.wfile.write(bytes(code, "utf-8"))

        client_address = self.redirect_uri.rsplit(":", maxsplit=1)
        client_address[0] = client_address[0].split("://", maxsplit=1)[1]
        client_address[1] = int(client_address[1]) if len(client_address) > 1 else 80

        # gets user consent and retrieves the authorization code
        server = HTTPServer(tuple(client_address), RequestHandler)

        webbrowser.open(response_uri, new=2)

        server.handle_request()
        server.server_close()

        return response

    def get_access_token(self, code: str):
        """Retrieves the access token from the authorization code following the Authorization Code Flow.

        See:
            https://developers.google.com/identity/protocols/oauth2/web-server?hl=en#httprest_3.

        Example:
            >>> this.get_access_token(self.authentificate())
            >>> "1/fFAGRNJru1FTz70BzhT3Zg"

        Args:
            code (str): the authorization code.

        Returns:
            str: the access token if the request was a success.
        """
        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        response = self.router.request("POST", "token", header, **params)
        print("granted scopes:", response["scope"].split(" "))
        print(response)

        return response["access_token"]

    def refresh_access_token(self, refresh_token: str):
        """Refreshes the access token from the refresh token.

        See:
            https://developers.google.com/youtube/v3/guides/auth/installed-apps?hl=en#offline for refreshing token.

        Args:
            refresh_token (str): the refresh token.

        Returns:
            str: the access token if the request was a success.
        """
        header = {"Accept": "application/json"}
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        return self.router.request("POST", "token", header, **params)["access_token"]

    def __request_header(self, /, acces_token: bool = True, **kwargs) -> Dict[str, str]:
        """Constructs and returns the request header.

        Args:
            acces_token (bool, optional): appends the access token to the header if `True`. Defaults to `True`.
            **kwargs: the additional header attributes.

        Returns:
            Dict[str, str]: the common request header with the specified attributes.
        """
        header = {"Content-Type": "application/json; charset=UTF-8", "Accept": "application/json", **kwargs}

        if acces_token and self.access_token:
            header["Authorization"] = f"Bearer {self.access_token}"

        return header

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

        return [(c["snippet"]["title"], c["id"]) for c in response["items"] if c["snippet"]["assignable"]]

    def is_category(self, category: str = "22") -> bool:
        """Tells if the specified category exists.

        Args:
            category (str, optional): the category id. Defaults to "22".

        Returns:
            bool: True if the category exists, False in case videoCategoryNotFound is raised.
        """
        header = self.__request_header()
        params = {"part": "snippet", "id": category}

        try:
            self.router.request("GET", "categories", header, return_json=False, **params)
        except HTTPError:
            return False
        return True

    # pylint: disable=too-many-arguments
    def upload_video(
        self, filename: str, title: str, description: str, category: str, tags: Optional[List[str]] = None
    ):
        """Uploads a video to Youtube from the specified file.

        See:
            https://developers.google.com/youtube/v3/guides/uploading_a_video?hl=en for the upload process.
            https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol?hl=en for resumable upload.
            https://developers.google.com/youtube/v3/docs/videos?hl=en#resource for the video resource.

        Args:
            filename (str): the path of the file to upload.
            title (str): the title of the video.
            description (str): the description of the video.
            category (str): the category id of the video as a string.
            tags (Optional[List[str]], optional): the tags of the video. Defaults to None.
        """
        with open(filename, "rb") as file:
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category,
                    # "thumbnails": {
                    #     "default": {"url": "https://i.ytimg.com/vi/3jWRrafhO7M/default.jpg", "width": 120, "height": 90}
                    # },
                },
                "status": {
                    "privacyStatus": PrivacyStatus.PRIVATE.value,
                    "embeddable": True,
                    "license": "youtube",
                },
            }

            print("body:", body)

            header = self.__request_header()
            header["Content-Length"] = str(sys.getsizeof(body))  # the number of bytes provided in the request body
            header["Content-Type"] = "application/json; charset=UTF-8"  # the MIME type of the body of the request
            header["X-Upload-Content-Length"] = str(os.fstat(file.fileno()).st_size)  # the size of the video in bytes
            header["X-Upload-Content-Type"] = "video/mp4"  # the MIME type of the video

            print("header", header)

            params = {"part": "snippet,status,contentDetails", "uploadType": "resumable"}

            # TODO add body to request

            response = self.router.request("POST", "resumable_upload", header, body, return_json=False, **params)
            session_uri: str = response.headers["Location"]

            header["Content-Type"] = header.pop("X-Upload-Content-Type")
            header["Content-Length"] = header.pop("X-Upload-Content-Length")

            files = {"file": file}

            print(session_uri)
            exit(0)

            # response = self.router.request("PUT", session_uri, header, files=files, **body)

        print(header, params, body)

        exit(0)

    def test(self, filename: str, title: str, description: str, category: str, tags: Optional[List[str]] = None):
        with open(filename, "rb") as file:
            header = self.__request_header()
            header["Content-Type"] = "video/mp4"
            header["Content-Length"] = str(os.fstat(file.fileno()).st_size)

            params = {"part": "snippet,status,contentDetails", "notifySubscribers": True}
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category,
                    "thumbnails": {},
                },
                "status": {
                    "privacyStatus": PrivacyStatus.PRIVATE.value,
                },
            }
            files = {"file": file}
            response = self.router.request("POST", "upload", header, body, files, **params)
            print(response)
        # TO do resumable upload
        # https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol?hl=fr
