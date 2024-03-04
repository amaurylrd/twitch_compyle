#!/usr/bin/env python3

# ********************************************************************************
# *     This software is licensed as described in the file LICENSE, which        *
# *     you should have received as part of this distribution. The terms         *
# *     are also available at gnu.org/licenses/license-list.html.                *
# ********************************************************************************


import argparse
import logging
import pathlib
from os import getenv
from typing import Any, Dict

import toml

from compyle.actions import collect
from compyle.actions.edit import edit
from compyle.settings import DEBUG

DEFAULT_REPORT_FOLDER = "reports/"
DEFAULT_VIDEO_FOLDER = "videos/"

def main():
    # defines the logging levels from the least verbose to the most
    levels = (logging.WARNING, logging.INFO, logging.DEBUG)

    # extracts the project information from the pyproject.toml file
    with open("pyproject.toml", encoding="utf-8") as file:
        section: Dict[str, Any] = toml.load(file)["tool"]["poetry"]
        # all requested keys are required in a valid pyproject.toml file
        name, description, version = (section[key] for key in ["name", "description", "version"])

    # creates the parser for the program arguments
    parser = argparse.ArgumentParser(description=description, epilog=f"{name} {version}")
    version_argument: argparse.Action = parser.add_argument("-V", "--version", action="version", version=version)
    version_argument.help = f"{version_argument.help} ({version})"
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="increase the verbosity (default: WARNING, -v: INFO, -vv: DEBUG)",
        default=len(levels) - 1 if DEBUG else 0,
    )

    # creates the subparser for the sub commands
    subparser: argparse._SubParsersAction = parser.add_subparsers(help="select the action to perform", required=True)

    # the parser for the command 'collect'
    collect.get_parser(subparser) # TODO module action, method collect

    # the parser for the command 'edit'
    # TODO faire le get_parser de edit
    parser_edit: argparse.ArgumentParser = subparser.add_parser("edit", aliases=["e"])  # TODO add description
    parser_edit.set_defaults(func=edit)
    parser_edit.add_argument(
        "-in",
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        metavar="FILE | DIRECTORY",
        help="specify the input path where to import the data from",
        default=argparse.SUPPRESS if getenv("MONGO_DB_URI") else DEFAULT_REPORT_FOLDER,
    )
    parser_edit.add_argument(
        "-out",
        "--output",
        type=pathlib.Path,  # TODO pathlib.Path doesn't keep the trailing slash
        metavar="FILE | DIRECTORY",
        help="specify the output path where to store the metafile about the video",
        default=argparse.SUPPRESS if getenv("MONGO_DB_URI") else DEFAULT_VIDEO_FOLDER,
    )

    # the parser for the command 'publish'
    parser_publish: argparse.ArgumentParser = subparser.add_parser("publish", aliases=["p"])  # TODO add description
    parser_publish.set_defaults(func=None)  # TODO set the function
    parser_publish.add_argument(
        "-in",
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        metavar="FILE | DIRECTORY",
        help="specify the input path where to retrieve the video data from",
        default=argparse.SUPPRESS if getenv("MONGO_DB_URI") else DEFAULT_VIDEO_FOLDER,
    )

    # parses the arguments present in the command line
    kwargs: Dict[str, Any] = dict(parser.parse_args()._get_kwargs())  # pylint: disable=protected-access

    # sets the logging level
    logging.basicConfig(level=levels[min(kwargs.pop("verbose"), len(levels) - 1)])

    return kwargs.pop("func")(**kwargs)


if __name__ == "__main__":
    main()
