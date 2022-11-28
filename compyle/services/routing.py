# pylint: disable=line-too-long, too-few-public-methods, unbalanced-tuple-unpacking

from collections.abc import Iterable
from typing import Any, Optional, Set
from urllib.parse import urlencode, urlparse, urlunparse

import requests

from compyle.utils.enums import Enum


class Endpoint:
    def __init__(self, base_url: str, slug: str, *, req=None, opt=None):
        def validate_urls(*args):
            for arg in args:
                if not isinstance(arg, str):
                    raise TypeError(f"String excpected, wrong type provided, found {type(arg)}")

            return args

        self.__base_url, self.__slug = validate_urls(base_url, slug)

        def validate_params(*args):
            args = [*args]
            for i, arg in enumerate(args):
                if arg is None:
                    args[i] = set()
                else:
                    if not isinstance(arg, Iterable):
                        raise TypeError(f"Iterable excpected, wrong type provided, found {type(arg)}")

                    if arg and not all(isinstance(item, str) for item in arg):
                        raise TypeError("Iterable of strings excpected, wrong type provided")
                    args[i] = set(arg)

            if any(arg for arg in args) and set.intersection(*args):
                raise ValueError("Required and optional parameters must be disjoint")

            return args

        self.__required_params, self.__optional_params = validate_params(req, opt)

    @property
    def base_url(self) -> str:
        return self.__base_url

    @property
    def slug_url(self) -> str:
        return self.__slug

    @property
    def required_params(self) -> Set[str]:
        return self.__required_params

    @property
    def optional_params(self) -> Set[str]:
        return self.__optional_params

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

        if not all(param in noramlized for param in self.required_params):
            raise ValueError(f"Missing required non-null parameters in {self.required_params.difference(noramlized)}")

        components = list(urlparse(self.base_url, allow_fragments=False))
        components[2] += self.slug_url
        components[4] = urlencode(noramlized)

        return urlunparse(components)


class Method(Enum):
    GET, POST, PUT, PATCH, DELETE = range(5)

    @property
    def func(self):
        return getattr(requests, self.name.lower())

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return self.func.__repr__()


class Router:
    def __init__(self, *, trailing_slash=True):
        self.__routes = {}
        self.__trailing_slash = trailing_slash

    def __str__(self):
        return str(self.__routes)

    def register(self, namespace: str, endpoint: Endpoint):
        """Registers the specified endpoint at the specified namespace.

        Example:
            >>> routes = Router()
            >>> routes.register("auth", Endpoint("https://api.twitch.tv/helix", "/token", req=["client_id", "client_secret", "grant_type"]))

        Args:
            namespace (str): the key used for this route.
            endpoint (Endpoint): the value paired to this key.

        Raises:
            ValueError: if the specified Endpoint is null.
        """
        if not endpoint:
            raise ValueError("The specified Endpoint must not be null")

        self.__routes[namespace] = endpoint

    def is_registered(self, namespace: str) -> bool:
        """Tells if the specified namespace is in the dictionary.

        Args:
            namespace (str): the namespace to be tested.

        Returns:
            bool: `True` if namespace is present, `False` otherwise.
        """
        return namespace in self.__routes

    def route(self, namespace: str, **query) -> Optional[str]:
        """Gets the route for the specified namespace if it is present, else None.

        See:
            :func:`~Endpoint.build_url`.

        Args:
            namespace (str): the namespace to be fetched.
            **query (dict): the parameters of the query.

        Returns:
            Optional[str]: the resulting url or None if namespace is absent of the dictionary.
        """
        if namespace not in self.__routes:
            return None

        endpoint: Endpoint = self.__routes.get(namespace)
        url: str = endpoint.build_url(**query)

        if self.__trailing_slash and url[-1] != "/":
            return url + "/"

        if not self.__trailing_slash and url[-1] == "/":
            return url[:-1]

        return url

    def request(self, method: str, namespace: str, header: dict, **params) -> Any:
        """Requests the specified url with the specified HTTP method and query parameters.

        Args:
            method (str): the HTTP method to be used.
            namespace (str): the namespace to be fetched.
            header (dict): the header to be used for the HTTP request.

        Raises:
            ValueError: if the specified method in not a valid HTTP method.
            ValueError: if the specified namespace is not registered.
            requests.HTTPError: if the HTTP request fails.

        Returns:
            Any: the json-encoded content of the response.
        """
        if method not in Method.__members__:
            raise ValueError(f"Invalid method {method}, expected one of {Method.__keys__}")

        if namespace not in self.__routes:
            raise ValueError("The specified route is not registered")

        url: str = self.route(namespace, **params)
        response: requests.Response = Method[method](url, headers=header, timeout=None)

        response.raise_for_status()

        return response.json()


class Routable:
    __router = Router(trailing_slash=False)

    @property
    def router(self):
        return self.__router
