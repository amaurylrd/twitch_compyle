#!/usr/bin/env python3

import argparse
import inspect
import logging
import pathlib

# import pathlib
from os import getenv
from typing import Any, Dict

import toml

# import compyle.actions
from compyle.actions import *

# from compyle.preloader import launch_after_preload

DEFAULT_REPORT_FOLDER = "reports/"
DEFAULT_VIDEO_FOLDER = "videos/"


def main():
    # defines the logging levels from the least verbose to the most
    levels = (logging.WARNING, logging.INFO, logging.DEBUG)

    # extracts the project infos from the pyproject.toml file
    with open("pyproject.toml", encoding="utf-8") as file:
        section: Dict[str, Any] = toml.load(file)["tool"]["poetry"]
        name, description, version = (keyword for keyword in section if keyword in ["name", "description", "version"])

    # creates the parser for the program arguments
    parser = argparse.ArgumentParser(description=description, epilog=f"{name} {version}")
    parser.add_argument("-V", "--version", action="version", version=version)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="increase the verbosity (default: WARNING, -v: INFO, -vv: DEBUG)",
        default=len(levels) - 1 if getenv("DEBUG") in ["True", "true"] else 0,
    )

    # creates the subparser for the sub commands
    subparser: argparse._SubParsersAction = parser.add_subparsers(help="select the action to perform", required=True)

    # the parser for the command 'collect'
    parser_collect: argparse.ArgumentParser = subparser.add_parser(
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
    parser_collect.set_defaults(func=collect.collect)
    parser_collect.add_argument(
        "-out",
        "--output",
        type=pathlib.Path,  # TODO pathlib.Path doesn't keep the trailing slash
        metavar="FILE | DIRECTORY",
        help="specify the output path where to store the report (all path elements will be created at need)",
        default=argparse.SUPPRESS if getenv("MONGO_DB_URI") else DEFAULT_REPORT_FOLDER,
    )

    # the parser for the command 'edit'
    parser_edit: argparse.ArgumentParser = subparser.add_parser("edit", aliases=["e"])  # TODO add description
    parser_edit.set_defaults(func=None)  # TODO set the function
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
    kwargs: Dict[str, Any] = {key: value for key, value in parser.parse_args()._get_kwargs()}

    # sets the logging level
    logging.basicConfig(level=levels[min(kwargs.pop("verbose"), len(levels) - 1)])

    return kwargs.pop("func")(**kwargs)


if __name__ == "__main__":
    main()
