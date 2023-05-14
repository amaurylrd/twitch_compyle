from os import getenv
from typing import Any, Dict, Optional

from compyle.services.routing import Routable
from compyle.utils.descriptors import deserialize


# https://datatracker.ietf.org/doc/html/rfc6749
class Service(Routable):
    def __init__(self, routes: Dict[str, Any], client_id: str, client_secret: str):
        """Initializes a new instance of the API client configured from the specified objet.

        Params:
            routes (Dict[str, Any]): the routes description.
            client_id (str): the client ID.
            client_secret (str): the client secret.
        """
        # checks if the service description contains all the mandatory routes
        if mandatory_routes := [route for route in ["auth"] if route not in routes.keys()]:
            raise ValueError("The service description is missing the following mandatory routes: " + mandatory_routes)

        # this.__validate_credentials(client_id, client_secret)
        # if not client_id or not client_secret:
        #     raise ValueError("The client ID and secret are required fields.")

        # retrieves the routes from the JSON object
        super().__init__(routes)

        # retrieves the client id and secret and generates a new client access token
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._access_token: str = self.get_new_access_token()

    @classmethod
    def from_json(cls, routes: str, client_id: str, client_secret: str) -> "Service":
        """Initializes a new instance of the API client configured from the specified file.

        Params:
            routes (Dict[str, Any]): the filename of the JSON containing the routes description.
            client_id (str): the client ID.
            client_secret (str): the client secret.
        """
        return cls(deserialize(routes), client_id, client_secret)

    def from_dict(self) -> "Service":
        pass

    # @__init__.register
    # def _(self, routes: str, client_id: str, client_secret: str):
    #     """Initializes a new instance of the API client configured from the specified file.

    #     Params:
    #         routes (Dict[str, Any]): the filename of the JSON containing the routes description.
    #         client_id (str): the client ID.
    #         client_secret (str): the client secret.
    #     """
    #     self.__init__(self, deserialize(routes), client_id, client_secret)

    @property
    def client_id(self) -> Optional[str]:
        """Gets the OAuth 2 client ID.

        Returns:
            Optional[str]: the OAuth 2 client ID.
        """
        return self._client_id

    @property
    def client_secret(self) -> Optional[str]:
        """Gets the OAuth 2 client secret.

        Returns:
            Optional[str]: the OAuth 2 client secret.
        """
        return self._client_secret

    @property
    def access_token(self) -> Optional[str]:
        """Gets the OAuth 2 access token.

        Returns:
            Optional[str]: the OAuth 2 access token.
        """
        return self._access_token

    def get_new_access_token(self) -> Any:
        """Gets a new client access token from API.

        Example:
            >>> self.get_new_access_token()
            >>> {'access_token': 'cfabdegwdoklmawdzdo98xt2fo512y', 'expires_in': 3600, 'token_type': 'bearer'}

        Returns:
            Any: the response deserialized as JSON if the request was successful, raises an error otherwise.
        """
        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        params = {"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"}

        return self.router.request("POST", "auth", header, **params)["access_token"]

    # TODO faire le request header


class Test(Service):
    def __init__(self):
        super().__init__(
            "compyle/services/routes/twitch.json", getenv("TWITCH_APP_CLIENT_ID"), getenv("TWITCH_APP_CLIENT_SECRET")
        )


x = Test()
