import json
from typing import Dict, Any


def deserialize(path: str) -> Any:
    """Loads the JSON object from the specified file.

    Params:
        path (str): the path to the JSON file.

    Returns:
        Any: the JSON object.
    """
    with open(path, "r", encoding="utf8") as file:
        return json.load(file)


def serialize(path: str, _object: Dict[str, Any] = None):
    """Saves the JSON object to the specified file replacing its content.

    Params:
        path (str): the location where to store the JSON object.
        _object (Dict[str, Any]): the object to be saved.
    """
    if path and _object:
        with open(path, "w", encoding="utf8") as file:
            json.dump(_object, file)
