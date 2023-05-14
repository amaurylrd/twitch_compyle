from http.server import BaseHTTPRequestHandler, HTTPServer
from os import getenv
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse
import webbrowser

from compyle.services.routing import Routable
from compyle.utils.descriptors import deserialize
from compyle.utils.enums import Enum


class PrivacyStatus(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class YoutubeApi(Routable):
    """This class implements the Youtube data API v3 and OAuth 2.0 for authentication.

    See:
        https://console.cloud.google.com/apis/library/youtube.googleapis.com
    """

    def __init__(self):
        """Initializes a new instance of the Youtube API client."""
        # retrieves the routes description from the JSON file
        super().__init__(deserialize("compyle/services/routes/youtube.json"))

        # retrieves the client id and secret redirect url from the environment variables
        self.client_id: Optional[str] = getenv("YOUTUBE_APP_CLIENT_ID")
        self.client_secret: Optional[str] = getenv("YOUTUBE_APP_CLIENT_SECRET")
        self.redirect_uri: str = getenv("YOUTUBE_APP_REDIRECT_URI", "http://localhost:3000")

        # checks if the client id and secret are specified
        if not self.client_id or not self.client_secret:
            raise ValueError("The client id and secret must be specified in the environment variables.")

        # retrieves the autorization code from authentification service
        user_email_address: Optional[str] = getenv("YOUTUBE_APP_EMAIL_ADDRESS")
        autorization_code: str = self.authentificate(user_email_address)

        code = input("Enter the authorization code: ")
        self.access_token = self.get_access_token(code)

    # pylint: disable=line-too-long
    def authentificate(self, login_hint: str) -> str:
        """Redirect the user to Google's OAuth 2.0 server to initiate the authentication and authorization process.
        Google's OAuth 2.0 server authenticates the user and obtains consent from the user for your application to access the requested scopes.
        The response is sent back to your application using the redirect URL you specified.

        See:
            https://developers.google.com/identity/protocols/oauth2/web-server?hl=en#httprest_2
            https://developers.google.com/identity/protocols/oauth2/scopes#youtube for scopes

        Returns:
            str: the authorization code
        """
        params = {
            "client_id": self.client_id,
            "scope": "https://www.googleapis.com/auth/youtube.upload",
            "access_type": "offline",
            "include_granted_scopes": "true",
            "response_type": "code",
            "state": "state_parameter_passthrough_value",
            "redirect_uri": self.redirect_uri,
            "prompt": "consent",
        }

        if login_hint:
            params["login_hint"] = login_hint

        response = self.router.request("HEAD", "auth", {}, **params, return_json=False)
        response_uri = response.headers.get("Location") or response.url

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                code: str = parse_qs(urlparse(self.path).query)["code"][0]
                self.send_response(200)
                self.send_header("test", "text/html")
                self.end_headers()
                self.wfile.write(bytes(code, "utf-8"))

        client_address = self.redirect_uri.rsplit(":", maxsplit=1)
        client_address[0] = client_address[0].split("://", maxsplit=1)[1]
        client_address[1] = int(client_address[1])
        server = HTTPServer(tuple(client_address), RequestHandler)

        webbrowser.open(response_uri, new=2)

        server.handle_request()
        server.server_close()

        return response

    def get_access_token(self, code: str):
        """Retrieves the access token from the authorization code following the Authorization Code Flow.

        See:
            https://developers.google.com/identity/protocols/oauth2/web-server?hl=en#httprest_3

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

        return self.router.request("POST", "token", header, **params)["access_token"]

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
        """_summary_

        See:
            https://developers.google.com/youtube/v3/guides/uploading_a_video?hl=en

        Args:
            filename (_type_): _description_
            title (_type_): _description_
            description (_type_): _description_
            tags (_type_): _description_
            category (_type_): _description_
        """
        # 256 Go
        # Types MIME de médias acceptés : video/*, application/octet-stream

        # TODO Resumable Uploads Proto
        # https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol?hl=fr
        header = self.__request_header()

        body = {
            "snippet": {"title": title, "description": description, "tags": tags, "categoryId": category},
            "status": {"privacyStatus": PrivacyStatus.PRIVATE},
        }
        files = None
        values = {"DB": "photcat", "OUT": "csv", "SHORT": "short"}
        with open("file.txt", "rb") as file:
            files = {"upload_file": file}

        # r = requests.post(url, files=files, data=values)
        # part = snippet,status
        # notifySubscribers = True
