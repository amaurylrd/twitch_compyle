from enum import Enum as _Enum
from typing import KeysView


class Enum(_Enum):
    @classmethod
    @property
    def __keys__(cls) -> KeysView[str]:
        return cls.__members__.keys()
