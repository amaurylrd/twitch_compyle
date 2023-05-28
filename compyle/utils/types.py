from enum import Enum as _Enum
from typing import KeysView


class Enum(_Enum):
    @classmethod
    @property
    def __keys__(cls) -> KeysView[str]:
        return cls.__members__.keys()


class Singleton(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in Singleton.__instances:
            Singleton.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return Singleton.__instances[cls]


# class Factory(type)
# class NoPublicConstructor(type):
#     """Metaclass that ensures a private constructor

#     If a class uses this metaclass like this:

#         class SomeClass(metaclass=NoPublicConstructor):
#             pass

#     If you try to instantiate your class (`SomeClass()`),
#     a `TypeError` will be thrown.
#     """

#     def __call__(cls, *args, **kwargs):
#         raise TypeError(
#             f"{cls.__module__}.{cls.__qualname__} has no public constructor"
#         )

#     def _create(cls: Type[T], *args: Any, **kwargs: Any) -> T:
#         return super().__call__(*args, **kwargs)
