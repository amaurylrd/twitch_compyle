import enum
import typing


class Enum(enum.Enum):
    @classmethod
    @property
    def __keys__(cls) -> typing.KeysView[str]:
        return cls.__members__.keys()
