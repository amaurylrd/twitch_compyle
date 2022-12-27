from functools import wraps


def default_kwargs(**defaults):
    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            defaults.update(kwargs)
            return func(*args, **defaults)

        return _wrapper

    return _decorator


def call_before_after(action, *action_args, **action_kwargs):
    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            action(*action_args, **action_kwargs)
            result = func(*args, **kwargs)
            action(*action_args, **action_kwargs)
            return result

        return _wrapper

    return _decorator
