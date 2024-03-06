import argparse
import datetime
import inspect
import os
import pathlib
from typing import Optional

from compyle.databases.mongo import MongoDB
from compyle.services.twitch import TwitchAPI
from compyle.utils.descriptors import serialize
from main import DEFAULT_REPORT_FOLDER


def get_parser(subparser: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = subparser.add_parser(
        "collect",
        aliases=["c"],
        description=inspect.cleandoc(
            """
            collect:
                1) retrieve clips data from the public Twitch API
                2) parse, select and normalize the data
                3) save the parsed result in MongoDB database or file
            """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.set_defaults(func=collect)
    parser.add_argument(
        "-out",
        "--output",
        nargs="?",
        type=pathlib.Path,
        metavar="FILE | DIRECTORY",
        help=inspect.cleandoc(
            """
            specify the output path where to store the report (all path elements will be created at need),
            if not specified the report will be stored in the configured database
            """
        ),
        required=os.getenv("MONGO_DB_URI") is None,
        default=argparse.SUPPRESS,
        const=DEFAULT_REPORT_FOLDER,
    )

    # argparse.SUPPRESS if os.getenv("MONGO_DB_URI") else
    return parser


# TODO > game_name et period des settings
# pylint: disable=line-too-long
def collect(*, output: Optional[pathlib.Path] = None, game_name: str = "League of Legends", period: int = 2):
    """Collects the clips for the specified game and period via the Twitch public API.

    Args:
        output (Optional[pathlib.Path], optional): the destination path where to store the clips data. Defaults to None. If None, the clips data will be stored in the mongoDB database.
        game_name (str, optional): the name of the game to retrieve the clips from. Defaults to "League of Legends".
        period (int, optional): the past period (in days) to retrieve the clips from. Defaults to 2.
    """
    # initializes the Twitch API client
    twitch_api = TwitchAPI()

    # retrieves the clips for the specified game and period
    game_name = "Minecraft"
    game_id = twitch_api.get_game_id(game_name)
    clips = twitch_api.get_game_clips(game_id, period=period)

    if not output:
        # stores the clips data to the database
        with MongoDB() as mongo_db:
            mongo_db.insert_documents("clips", clips)
    else:
        output = output.__str__()
        # stores the clips data in the filesystem
        if output.endswith("/") or os.path.isdir(output):
            output = os.path.join(output, game_name)
            filename = f'{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.json'
        elif "/" in output:
            output, filename = output.rsplit("/", maxsplit=1)
        else:
            output, filename = "", output

        # creates the output folders that does not exist
        if output:
            os.makedirs(output, exist_ok=True)

        # serializes the clips data to the data file
        serialize(os.path.join(output, filename), clips)
