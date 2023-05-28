import datetime
import os
from typing import Optional

from compyle.services.controllers.twitch import TwitchApi
from compyle.utils.descriptors import serialize

DEFAULT_FOLDER = "reports/"

# TODO > game_name et period des settings
# TODO > DEFAULT_FOLDER déplacer ?


def collect(*, output: str = DEFAULT_FOLDER, game_name: str = "League of Legends", period: int = 2) -> str:
    """Collects the clips for the specified game and period via the Twitch public API.

    Args:
        output (str, optional): the destination path where to store the clips data. Defaults to DEFAULT_FOLDER.
        game_name (str, optional): the name of the game to retrieve the clips from. Defaults to "League of Legends".
        period (int, optional): the period in days to retrieve the clips from. Defaults to 2.

    Returns:
        str: the path to the output file.
    """
    # initializes the Twitch API client
    twitch_api = TwitchApi()

    # retrieves the clips for the specified game and period
    game_id = twitch_api.get_game_id(game_name)
    clips = twitch_api.get_game_clips(game_id, period=period)

    # checks if the specified path is a file or a directory
    if output.endswith("/") or os.path.isdir(output):
        output = os.path.join(output, game_name)
        filename = f'{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.json'
    else:
        output, filename = output.rsplit("/", maxsplit=1) if "/" in output else "", output

    # creates the output folders that does not exist
    if output:
        os.makedirs(output, exist_ok=True)
    output = os.path.join(output, filename)

    # serializes the clips data to the data file
    serialize(output, clips)

    # returns the output file path
    return output


def get_latest_file(path: os.PathLike) -> Optional[str]:
    """Returns the most recent file that has been created in the specified folder path.

    Args:
        path (os.PathLike): the path to the directory.

    Returns:
        Optional[str]: the path to the most recent file if any, otherwise `None`.
    """
    # checks if the specified path is an existing directory
    if path and os.path.isdir(path):
        # gets the file in the specified path with the latest creation time
        return max((os.path.join(path, basename) for basename in os.listdir(path)), key=os.path.getctime, default=None)
    return None
