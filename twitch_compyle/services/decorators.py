from functools import wraps


def default_kwargs(**defaults):
    def _decorator(func):
        @wraps(func)
        def _wrapper(instance, *args, **kwargs):
            defaults.update(kwargs)
            return func(instance, *args, **defaults)

        return _wrapper

    return _decorator


class DecoratorError(Exception):
    def __init__(self):
        super().__init__("An error occurred while handling the decorating of the function")
