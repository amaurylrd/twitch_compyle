from collections.abc import Iterable
from typing import Optional, Set
from urllib.parse import urlencode, urlparse, urlunparse


class Endpoint:
    def __init__(self, base_url: str, slug: str, *, req=None, opt=None):
        def validate_urls(*args):
            for arg in args:
                if not isinstance(arg, str):
                    raise TypeError(f"string excpected, wrong type provided, found {type(arg)}")

            return args

        self.__base_url, self.__slug = validate_urls(base_url, slug)

        # pylint: disable=unbalanced-tuple-unpacking
        def validate_params(*args):
            args = [*args]
            for i, arg in enumerate(args):
                if arg is None:
                    args[i] = set()
                else:
                    if not isinstance(arg, Iterable):
                        raise TypeError(f"iterable excpected, wrong type provided, found {type(arg)}")

                    if arg and not all(isinstance(item, str) for item in arg):
                        raise TypeError("iterable of strings excpected, wrong type provided")
                    args[i] = set(arg)

            if any(arg for arg in args) and set.intersection(*args):
                raise ValueError("required and optional parameters must be disjoint")

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
            raise ValueError(f"Missing at least one required parameter in {self.required_params}")

        if not all(param in noramlized for param in self.required_params):
            raise ValueError(f"Missing required parameters in {self.required_params.difference(noramlized)}")

        components = list(urlparse(self.base_url))
        components[2] = self.slug_url
        components[4] = urlencode(noramlized)

        return urlunparse(components)


class Router:
    def __init__(self, *, trailing_slash=True):
        self.__routes = {}
        self.__trailing_slash = trailing_slash

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
            raise ValueError("specified Endpoint must not be null")

        self.__routes[namespace] = endpoint

    def route(self, namespace: str, *args) -> Optional[str]:
        """Gets the route for the specified namespace if it is present, else None.

        See:
            :func:`~Endpoint.build_url`.

        Args:
            namespace (str): the namespace to be fetched.

        Returns:
            Optional[str]: the resulting url or None if namespace is absent of the dictionary.
        """
        if not (endpoint := self.__routes.get(namespace)):
            return None

        url = endpoint.build_url(*args)

        if self.__trailing_slash and url[-1] != "/":
            return url + "/"

        if not self.__trailing_slash and url[-1] == "/":
            return url[:-1]

        return url


# pylint: disable=too-few-public-methods
class Routable:
    __router = Router(trailing_slash=False)

    @property
    def router(self):
        return self.__router
