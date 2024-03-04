import logging
from abc import ABC
from enum import IntEnum
from io import BufferedReader
from typing import Any, Callable, KeysView, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import urlretrieve

import requests
from requests.adapters import HTTPAdapter
from rest_framework import status
from urllib3.util import Retry

import compyle.services.routes

LOGGER = logging.getLogger(__name__)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


class Endpoint:
    """This class represents an endpoint for an API."""

    def __init__(self, base_url: str, slug: str, req: list[str] | None = None, opt: list[str] | None = None):
        """Constructs a new instance of the `Endpoint` class.

        Args:
            base_url (str): the base url of the request.
            slug (str): the slug of the request.
            req (list[str], optional): the list of required url parameters.
            opt (list[str], optional): the list of optional url parameters.

        Raises:
            ValueError: if the required and optional parameters are not disjoint.
        """
        self._base_url, self._slug = base_url, slug
        self._required_params, self._optional_params = set(req or []), set(opt or [])

        if self._required_params & self._optional_params:
            raise ValueError("Required and optional parameters must be disjoint")

    # pylint: disable=line-too-long
    def build_url(self, **query) -> str:
        """Builds the URL for the specified queryset.

        Example:
            >>> endpt = Endpoint("https://api.twitch.tv/helix", "/token", req=["client_id", "client_secret", "grant_type"])
            >>> url = endpt.build_url(client_id="hof5gwx0su6owfnys0yan9c87zr6t", client_secret="41vpdji4e9gif29md0ouet6fktd2", grant_type="client_credentials")
            >>> "https://api.twitch.tv/helix/token?client_id=hof5gwx0su6owfnys0yan9c87zr6t&client_secret=41vpdji4e9gif29md0ouet6fktd2&grant_type=client_credentials

        Args:
            **query (dict): the parameters of the query.

        Raises:
            ValueError: if any required parameter is not specified.

        Returns:
            str: the unparsed URL built with the normalized query parameters.
        """
        params = {k: query.get(k) for k in self._required_params | self._optional_params if k in query}

        # checks if all required parameters are present
        if len(params) < len(self._required_params) or any(param not in params for param in self._required_params):
            raise ValueError(f"Missing required non-null parameters in {self._required_params.difference(params)}")

        # builds the url with the normalized query
        components = list(urlparse(self._base_url, allow_fragments=False))
        components[2] += self._slug
        components[4] = urlencode(params)

        return urlunparse(components)

    @staticmethod
    def extract_url_params(url: str) -> list[Tuple[str, str]]:
        """Extracts the parameters from the specified url.

        Args:
            url (str): the url to extract the parameters from.

        Returns:
            list[Tuple[str, str]]: the list of parameters, as G-d intended.
        """
        return parse_qsl(urlparse(url).query, keep_blank_values=True)

    @staticmethod
    def add_url_params(url: str, **params) -> str:
        """Adds the specified parameters to the url.

        Args:
            url (str): the url to add the parameters to.
            **params: the parameters to be added.

        Returns:
            str: the url with the parameters added.
        """
        parts = urlparse(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True)).update(params)

        return urlunparse(parts._replace(query=urlencode(query)))


class Method(IntEnum):
    """This enum represents the HTTP methods supported by the API."""

    GET, POST, PUT, PATCH, DELETE, HEAD = range(6)

    @property
    def func(self) -> Callable[..., Any]:
        """Retrieve the partial function from its enum name.

        Returns:
            function: the function callable if the attribute exists, raises an error otherwise.
        """
        return getattr(requests, self.name.lower())

    def __call__(self, *args, **kwargs) -> requests.Response:
        """Calls the function associated with the enum.

        Returns:
            requests.Response: the result of the function.
        """
        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        """Returns the representation of the enum.

        Returns:
            str: the representation of the enum.
        """
        return self.func.__repr__()

    def __str__(self) -> str:
        """Returns the string representation of the enum.

        Returns:
            str: the string representation of the enum.
        """
        return self.func.__str__()


class Router:
    """This class represents a router for an API."""

    def __init__(self, *, trailing_slash: bool = True):
        """Constructs a new instance of the Router class.

        Args:
            trailing_slash (bool, optional): tells if the route are suffixed with a trailing slash. Defaults to True.
        """
        self._routes: dict[str, Endpoint] = {}
        self._trailing_slash: bool = trailing_slash

    def __str__(self) -> str:
        """Returns a string representation of the router.

        Returns:
            str: the list of registered routes.
        """
        return str(self._routes)

    # pylint: disable=line-too-long
    def register(self, namespace: str, endpoint: Endpoint):
        """Registers the specified endpoint at the specified namespace.

        Example:
            >>> routes = Router()
            >>> routes.register("auth", Endpoint("https://api.twitch.tv/helix", "/token", req=["client_id", "client_secret", "grant_type"]))

        Args:
            namespace (str): the key used for this route.
            endpoint (Endpoint): the value paired to this key.

        Raises:
            ValueError: if the specified namespace is empty or mistyped.
            ValueError: if the specified endpoint is null or mistyped.
        """
        # checks if the namespace is a non-empty string
        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError("The specified namespace is malformed")

        # checks if the endpoint is from the Endpoint class
        if not isinstance(endpoint, Endpoint):
            raise ValueError("The specified endpoint is malformed")

        self._routes[namespace] = endpoint

    def is_registered(self, namespace: str) -> bool:
        """Tells if the specified namespace is in the dictionary.

        Args:
            namespace (str): the namespace to be tested.

        Returns:
            bool: `True` if namespace is present in the routes, `False` otherwise.
        """
        return namespace in self._routes

    def get_registered(self) -> KeysView[str]:
        """Returns the namespace registered.

        Returns:
            KeysView[str]: the list of routes.
        """
        return self._routes.keys()

    def route(self, namespace: str, **query) -> str:
        """Gets the route for the specified namespace if it is present in the registered routes.

        See:
            :func:`~Endpoint.build_url`.

        Args:
            namespace (str): the namespace to be fetched.
            **query (dict): the parameters of the query.

        Raises:
            ValueError: if the specified namespace is not registered.

        Returns:
            str: the resulting url.
        """
        # checks if the namespace is registered
        if namespace not in self._routes:
            raise ValueError("The specified route is not registered")

        endpoint: Endpoint = self._routes[namespace]
        url: str = endpoint.build_url(**query)

        # adds a trailing slash if the option is specified and the url does not already end with a slash
        if self._trailing_slash and url[-1] != "/":
            return url + "/"

        # removes the trailing slash if the option is specified and the url ends with a slash
        if not self._trailing_slash and url[-1] == "/":
            return url[:-1]

        return url

    # pylint: disable=too-many-arguments
    def __request_with_retry(
        self,
        method: str,
        url: str,
        retries: int = 3,
        backoff: float = 0.5,
        jitter: float = 0.5,
        timeout: float | None = 2.0,
        **request,
    ) -> requests.Response:
        """Requests the specified url with the specified HTTP method and query parameters.

        Args:
            method (str): the HTTP method to be used.
            url (str): the URL to be requested.
            retries (int, optional): the number of retries. Defaults to 3.
            backoff (float, optional): the backoff factor in seconds. Defaults to 0.5.
            jitter (float, optional): the backoff jitter in seconds. Defaults to 0.5.
            timeout (float, optional): the request timeout in seconds. Defaults to 1.
            **request: the parameters to be used for the HTTP request.

        Raises:
            requests.exceptions.RequestException: if the request fails.

        Returns:
            requests.Response: the response of the request.
        """
        with requests.Session() as session:
            strategy = Retry(
                total=retries,
                backoff_factor=backoff,
                backoff_jitter=jitter,
                status_forcelist=[
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    status.HTTP_502_BAD_GATEWAY,
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    status.HTTP_504_GATEWAY_TIMEOUT,
                ],
            )
            adapter = HTTPAdapter(max_retries=strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            try:
                response = Method[method](url, **request, timeout=timeout)
                LOGGER.info(
                    "Request %s %s, respond with status %s in %.3fs",
                    method,
                    url.split("?", maxsplit=1)[0].split("/")[-1],
                    response.status_code,
                    response.elapsed.total_seconds(),
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as error:
                raise error

    # pylint: too-many-arguments
    def request(
        self,
        method: str,
        namespace: str,
        header: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        files: dict[str, BufferedReader] | None = None,
        *,
        return_json: bool = True,
        **params,
    ) -> requests.Response:
        """Requests the specified url with the specified HTTP method and query parameters.

        Args:
            method (str): the HTTP method to be used.
            namespace (str): the namespace to be fetched.
            header (dict[str, str], optional): the header to be used for the HTTP request. Defaults to `None`.
            body (dict[str, Any], optional): the body to be used for the HTTP request. Defaults to `None`.
            files (dict[str, BufferedReader], optional): the files to be used for the HTTP request. Defaults to `None`.
            return_json (bool, optional): flag to tell if the response is decoded to JSON. Defaults to `True`.
            **params: the additional parameters to be used for the HTTP request.

        Raises:
            ValueError: if the specified method in not a valid HTTP method.
            requests.exceptions.JSONDecodeError: if the response is not JSON valid.

        Returns:
            requests.Response: the response or the JSON-encoded content if the option is specified.
        """
        if method not in Method.__members__:
            raise ValueError(f"Invalid method {method}, expected one of {Method.__members__.keys()}")

        if method in (Method.GET.name, Method.HEAD.name):
            response = self.__request_with_retry(method, self.route(namespace, **params), headers=header)
        else:
            response = self.__request_with_retry(
                method, self.route(namespace, **params), headers=header, data=body, files=files
            )

        return response.json() if return_json else response


# pylint: disable=too-few-public-methods
class Routable(ABC):
    """This class contains an object `Router` and should be extended by `Routable` classes."""

    __router = Router(trailing_slash=False)

    def __init__(self):
        """Constructor for the abstract class `Routable`."""
        routes: dict[str, str] = getattr(compyle.services.routes, self.__class__.__name__.lower().replace("api", ""))

        for key, values in routes.items():
            self.router.register(key, Endpoint(**values))

        LOGGER.info("Registered routes for %s: %s", self.__class__.__name__, list(self.router.get_registered()))

    @property
    def router(self) -> Router:
        """Getter to access the router from child class.

        See:
            :func:`~Router.register`.
            :func:`~Router.route`.

        Returns:
            Router: the router for this instance.
        """
        return self.__router


def get_url_content(url: str) -> str:
    """Retrieves the specified url and returns its content into a temporary file on disk.

    Args:
        url (str): the url to be retrieved.

    Returns:
        str: the path to the newly created data file.
    """
    return urlretrieve(url)[0]  # nosec
