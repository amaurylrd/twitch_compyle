from enum import Enum as _Enum
from typing import Any, Dict, KeysView


class Enum(_Enum):
    @classmethod
    @property
    def __keys__(cls) -> KeysView[str]:
        return cls.__members__.keys()


class Singleton(type):
    __instances: Dict[str, "Singleton"] = {}

    def __call__(cls, *args, **kwargs) -> Any:
        if cls not in Singleton.__instances:
            Singleton.__instances[cls] = super().__call__(*args, **kwargs)
        return Singleton.__instances[cls]
