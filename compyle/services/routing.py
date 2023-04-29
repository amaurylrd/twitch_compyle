import logging
import time
from abc import ABC
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any, Dict, KeysView, Optional, Set
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from rest_framework import status

from compyle.utils.enums import Enum

LOGGER = logging.getLogger(__name__)


class Endpoint:
    """This class represents an endpoint for an API."""

    def __validate_urls(self, *args):
        """Validates that endpoint parameters such as base_url and slug are strings.

        Args:
            *args (tuple): the parameters of the endpoint.

        Raises:
            TypeError: if any parameter is not type str.
            ValueError: if any parameter is an empty str.

        Returns:
            tuple: the validated and normalized parameters.
        """
        args = [*args]
        for i, arg in enumerate(args):
            if not isinstance(arg, str):
                raise TypeError(f"String expected, wrong type provided at position {i}, found {type(arg)}")

            args[i] = arg.strip()
            # slug devrait etre opt, par defaut ""
            if not args[i]:
                raise ValueError(f"Non-empty string expected, wrong value provided at position {i}")

        return args

    def __validate_url_params(self, *args):
        """Validates that query parameters such as required and optional url parameters are sets of strings.

        Args:
            *args (tuple): the parameters of the query.

        Raises:
            TypeError: if any specified parameter is not an iterable.
            TypeError: if any element of iterable is not type str.
            ValueError: if required and optional parameters are not disjoint.

        Returns:
            tuple: the validated and normalized parameters.
        """
        # joins the required and optional url parameters lists into a single list
        args = [*args]
        for i, arg in enumerate(args):
            # sets the parameter to an empty set if not provided
            if arg is None:
                args[i] = set()
            else:
                if not isinstance(arg, Iterable):
                    raise TypeError(f"Iterable expected, wrong type provided at position {i}, found {type(arg)}")

                if arg and any(not isinstance(a, str) for a in arg):
                    raise TypeError("Iterable of strings expected, wrong type provided in the iterable")
                args[i] = set(arg)

        if any(args) and set.intersection(*args):
            raise ValueError("Required and optional parameters must be disjoint")

        return args

    # pylint: disable=unbalanced-tuple-unpacking
    def __init__(self, base_url: str, slug: str, *, req: Iterable = None, opt: Iterable = None):
        """Constructs a new instance of the Endpoint class.

        Args:
            base_url (str): the base url of the request.
            slug (str): the slug of the request.
            req (Iterable, optional): the list of required body parameters. Defaults to None.
            opt (Iterable, optional): the list of optional body parameters. Defaults to None.
        """
        self.__base_url, self.__slug = self.__validate_urls(base_url, slug)
        self.__required_params, self.__optional_params = self.__validate_url_params(req, opt)

    @property
    def base_url(self) -> str:
        """Getter to access the base of the request url.

        Returns:
            str: the base of the url.
        """
        return self.__base_url

    @property
    def slug_url(self) -> str:
        """Getter to access the slug attribute of the request url.

        Returns:
            str: the slug of the url.
        """
        return self.__slug

    @property
    def required_params(self) -> Set[str]:
        """Getter to access the required parameters specified at the creation.

        Returns:
            Set[str]: the set of required parameters, or an empty set if none were specified.
        """
        return self.__required_params

    @property
    def optional_params(self) -> Set[str]:
        """Getter to access the optional parameters specified at the creation.

        Returns:
            Set[str]: the set of optional parameters, or an empty set if none were specified..
        """
        return self.__optional_params

    # pylint: disable=line-too-long
    def build_url(self, **query) -> str:
        """Builds the url for the specified queryset.

        Example:
            >>> endpt = Endpoint("https://api.twitch.tv/helix", "/token", req=["client_id", "client_secret", "grant_type"])
            >>> url = endpt.build_url(client_id="hof5gwx0su6owfnys0yan9c87zr6t", client_secret="41vpdji4e9gif29md0ouet6fktd2", grant_type="client_credentials")
            >>> "https://api.twitch.tv/helix/token?client_id=hof5gwx0su6owfnys0yan9c87zr6t&client_secret=41vpdji4e9gif29md0ouet6fktd2&grant_type=client_credentials

        Args:
            **query (dict): the parameters of the query.

        Raises:
            ValueError: if any required parameter is not specified.

        Returns:
            str: the unparsed url.
        """
        noramlized = {k: query[k] for k in self.required_params | self.optional_params if k in query and query[k]}

        if len(noramlized) < len(self.required_params):
            raise ValueError(f"Missing at least one required non-null parameter in {self.required_params}")

        if any(param not in noramlized for param in self.required_params):
            raise ValueError(f"Missing required non-null parameters in {self.required_params.difference(noramlized)}")

        components = list(urlparse(self.base_url, allow_fragments=False))
        components[2] += self.slug_url
        components[4] = urlencode(noramlized)

        return urlunparse(components)


class Method(Enum):
    """This enum represents the HTTP methods supported by the API."""

    GET, POST, PUT, PATCH, DELETE, HEAD = range(6)

    @property
    def func(self) -> callable:
        """Retrieve the partial function from its enum name.

        Returns:
            function: the function callable if the attribute exists, raises an error otherwise.
        """
        return getattr(requests, self.name.lower())

    def __call__(self, *args, **kwargs) -> Any:
        """Calls the function associated with the enum.

        Returns:
            Any: the result of the function.
        """
        return self.func(*args, **kwargs)

    def __repr__(self) -> Any:
        """Returns the representation of the enum.

        Returns:
            Any: the representation of the enum.
        """
        return self.func.__repr__()


class Router:
    """This class represents a router for an API."""

    def __init__(self, *, trailing_slash: bool = True):
        """Constructs a new instance of the Router class.

        Args:
            trailing_slash (bool, optional): tells if the route are suffixed with a trailing slash. Defaults to True.
        """
        self.__routes: Dict[str, Endpoint] = {}
        self.__trailing_slash: bool = trailing_slash
        self.__status_page: str = None

    def __str__(self) -> str:
        """Returns a string representation of the router.

        Returns:
            str: the list of registered routes.
        """
        return str(self.__routes)

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
        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError("The specified namespace is malformed")

        if not isinstance(endpoint, Endpoint):
            raise ValueError("The specified endpoint is malformed")

        self.__routes[namespace] = endpoint

    def is_registered(self, namespace: str) -> bool:
        """Tells if the specified namespace is in the dictionary.

        Args:
            namespace (str): the namespace to be tested.

        Returns:
            bool: `True` if namespace is present in the routes, `False` otherwise.
        """
        return namespace in self.__routes

    def get_registered(self) -> KeysView[str]:
        """Returns the namespace registered.

        Returns:
            KeysView[str]: the list of routes.
        """
        return self.__routes.keys()

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
        if namespace not in self.__routes:
            raise ValueError("The specified route is not registered")

        endpoint: Endpoint = self.__routes[namespace]
        url: str = endpoint.build_url(**query)

        if self.__trailing_slash and url[-1] != "/":
            return url + "/"

        if not self.__trailing_slash and url[-1] == "/":
            return url[:-1]

        return url

    def __execute_request(self, method: str, url: str, header: Dict[str, str]) -> requests.Response:
        """Executes the specified HTTP request.

        Args:
            method (str): the HTTP method to be used.
            url (str): the url to be used for the HTTP request.
            header (dict): the header to be normalized and used for the HTTP request.

        Raises:
            ValueError: if the specified method in not a valid HTTP method.
            requests.exceptions.HTTPError: if the request failed.

        Returns:
            requests.Response: the response of the HTTP request.
        """
        if method not in Method.__members__:
            raise ValueError(f"Invalid method {method}, expected one of {Method.__keys__}")

        try:
            response: requests.Response = Method[method](
                url, headers={k.upper(): v for k, v in header.items()}, timeout=None
            )
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as error:
            raise error
        finally:
            LOGGER.debug(
                "Request %s %s, respond with %s in %.3fs",
                method,
                url.split("?", maxsplit=1)[0].split("/")[-1],
                response.status_code,
                response.elapsed.total_seconds(),
            )

    def __noramlized_response(self, response: requests.Response, jsonify: bool = True) -> Any:
        """Returns the response as JSON if the response is valid.

        Args:
            response (requests.Response): the response to be decoded.
            jsonify (bool, optional): tells if the response has to be decoded to JSON. Defaults to `True`.

        Raises:
            requests.exceptions.JSONDecodeError: if the response is not JSON valid.

        Returns:
            Any: the response or the JSON-encoded content if the option is specified.
        """
        try:
            return response.json() if jsonify else response
        except requests.exceptions.JSONDecodeError as error:
            raise error

    def request(self, method: str, namespace: str, header: Dict[str, str], *, json=True, **params) -> Any:
        """Requests the specified url with the specified HTTP method and query parameters.

        Args:
            method (str): the HTTP method to be used.
            namespace (str): the namespace to be fetched.
            header (dict): the header to be used for the HTTP request.
            json (bool): if the response is decoded to JSON.
            paramas (dict): the parameters of the query.

        Returns:
            Any: the response or the JSON-encoded content if the option is specified.
        """
        url: str = self.route(namespace, **params)
        response: requests.Response = self.__execute_request(method, url, header)

        backoff: float = 0.5  # in seconds
        max_retries: int = 3

        while response.status_code >= 500 and max_retries > 0:
            LOGGER.debug("The request failed number of retries left: %s", max_retries)
            LOGGER.debug("The backoff delay has been set to %.2s seconds", backoff)

            if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
                LOGGER.debug(
                    """You may check the API status page %sfor relevant updates and details on health
                    and incidents.""",
                    "(" + self.__status_page + ") " if self.__status_page else " ",
                )
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                epoch_timestamp: str = response.headers["Ratelimit-Reset"]
                reset: datetime = datetime.fromtimestamp(epoch_timestamp)
                delta: timedelta = reset - datetime.now()

                LOGGER.debug(
                    "The bucket runs out of points within the last minute, it will be reset to full under %f",
                    delta.total_seconds(),
                )
            else:
                time.sleep(backoff)
                response = self.__execute_request(method, url, header)

                backoff *= 2
                max_retries -= 1

        return self.__noramlized_response(response, json)

    def set_status_page(self, status_page: str) -> None:
        """Sets the status page with the specified url.

        Args:
            status_page (str): the status page to be set.
        """
        self.__status_page = status_page

    def get_status_page(self) -> Optional[str]:
        """Returns the status page.

        Returns:
            Optional[str]: the status page if set else None.
        """
        return self.__status_page


# pylint: disable=too-few-public-methods
class Routable(ABC):
    """This class contains an object Router and should be extended by routable classes."""

    __router = Router(trailing_slash=False)

    def __init__(self, routes: Dict[str, Any]):
        """Constructor for the abstract class Routable.

        Args:
            routes (Dict[str, Any]): the routes to be registered with their params.
        """
        for key, values in routes.items():
            if not self.router.get_status_page() and key == "status":
                self.router.set_status_page(values)
            else:
                self.router.register(key, Endpoint(**values))
        LOGGER.debug("Registered routes for %s: %s", self.__class__.__name__, list(self.router.get_registered()))

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
