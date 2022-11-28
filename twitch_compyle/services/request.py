from functools import partial, wraps

from aenum import Enum
from decorators import DecoratorError, default_kwargs
from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry
from routing import Routable, Router


# pylint: disable=too-few-public-methods
class HttpPooling:
    @default_kwargs(total=5, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504))
    def __init__(self, **kwargs):
        self.session = Session()
        retries = Retry(**kwargs)

        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))


class HttpMethod(Enum):
    POST, GET, PUT, PATH, DELETE = range(1, 6)

    __pool = HttpPooling()
    __ignore__ = ("__pool",)

    def __repr__(self):
        return self.value.__repr__()

    @property
    def value(self):
        return partial(getattr(self.__pool.session, self.name.lower()))

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)

    @classmethod
    def keys(cls):
        return cls.__members__.keys()


def request(method: str, namespace: str, append_token=True, **header):
    def _decorator(func):
        @wraps(func)
        def _wrapper(self: Routable, *args, **kwargs):
            if method not in HttpMethod.__members__:
                raise ValueError(f"Invalid method {method}, expected one of {HttpMethod.keys()}")

            router: Router = getattr(self, "router", None)

            if not (router and isinstance(router, Router) and router.is_registered(namespace)):
                raise ValueError("This decorator is designed to be placed to fast access router attribute")

            url: str = router.route(namespace, *args, **kwargs)
            response: Response = HttpMethod[method](url, headers=header, timeout=None)

            response.raise_for_status()
            serialized = result = response.json()

            if "data" in serialized:
                result: list = serialized["data"]

                while serialized["data"] and serialized["pagination"] is not None:
                    kwargs["after"] = serialized["pagination"]["cursor"]

                    url: str = router.route(namespace, *args, **kwargs)
                    response: Response = HttpMethod[method](url, headers=header, timeout=None)

                    serialized = response.json()
                    result.extend(serialized["data"])

            return func(self, result, *args, **kwargs)

        try:
            return _wrapper
        except Exception as exception:
            raise DecoratorError() from exception

    return _decorator
