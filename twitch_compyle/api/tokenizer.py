import json
from typing import Dict, Any


def deserialize_token(path: str) -> Any:
    """Loads the JSON object from the specified file.

    Params:
        path (str): the path to the JSON file.

    Returns:
        Any: the token as JSON object.
    """
    if path:
        with open(path, mode="r") as token_file:
            return json.load(token_file)


def serialize_token(path: str, token_object: Dict[str, Any] = None):
    """Saves the JSON object to the specified file replacing its content.

    Params:
        path (str): the location where to store the JSON object.
        token_object (Dict[str, Any]): the object to be saved.
    """
    if path and token_object:
        with open(path, mode="w") as token_file:
            json.dump(token_object, token_file)