import argparse
import logging
from os import getenv
import pathlib
from typing import Any, Dict

import toml

from compyle.actions import *

# from compyle.preloader import launch_after_preload

DEFAULT_REPORT_FOLDER = "reports/"
DEFAULT_VIDEO_FOLDER = "videos/"


def main():
    # TODO loads the settings from the env file

    # extracts the project infos from the pyproject.toml file
    with open("pyproject.toml", "r", encoding="utf-8") as file:
        project: Dict[str, Any] = toml.load(file)["tool"]["poetry"]
        name, description, version = project["name"], project["description"], project["version"]

    # creates the parser for the program arguments
    parser = argparse.ArgumentParser(description=description, epilog=f"{name} {version}")
    parser.add_argument("-V", "--version", action="version", version=version)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="increase the verbosity (default: WARNING, -v: INFO, -vv: DEBUG)",
        default=0 if getenv("DEBUG") in ["True", "true"] else 2,
    )

    # creates the subparser for the commands
    subparser: argparse._SubParsersAction = parser.add_subparsers(
        dest="action", help="select the action to perform", required=True
    )

    # the parser for the 'collect' action
    parser_collect: argparse.ArgumentParser = subparser.add_parser("collect")
    parser_collect.set_defaults(func=collect.collect)
    parser_collect.add_argument(
        "-out",
        "--output",
        type=pathlib.Path,
        metavar="FILE | DIRECTORY",
        help="specifiy the output path where to store the report",
        default=DEFAULT_REPORT_FOLDER,
    )

    # the parser for the 'edit' action
    parser_edit: argparse.ArgumentParser = subparser.add_parser("edit")
    parser_edit.set_defaults(func=None)  # TODO set the function
    parser_edit.add_argument(
        "-in",
        "--input",
        type=pathlib.Path,
        metavar="FILE | DIRECTORY",
        help="specifiy the input path where to import the data from",
        default=DEFAULT_REPORT_FOLDER,
    )
    parser_edit.add_argument(
        "-out",
        "--output",
        type=pathlib.Path,
        metavar="FILE | DIRECTORY",
        help="specifiy the output path where to store the metafile about the video",
        default=DEFAULT_VIDEO_FOLDER,
    )

    # the parser for the 'publish' action
    parser_publish: argparse.ArgumentParser = subparser.add_parser("publish")
    parser_publish.set_defaults(func=None)  # TODO set the function
    parser_publish.add_argument(
        "-in",
        "--input",
        type=pathlib.Path,
        metavar="FILE | DIRECTORY",
        help="specifiy the input path where to retrieve the video data from",
        default=DEFAULT_VIDEO_FOLDER,
    )

    # parses the arguments present in the command line
    args: argparse.Namespace = parser.parse_args()

    # sets the logging level
    levels = (logging.WARNING, logging.INFO, logging.DEBUG)
    logging.basicConfig(level=levels[min(args.verbose, len(levels) - 1)])

    # TODO run the action function
    exit(0)


# TODO faire un fichier de test
# def test():
#     import os

#     args = parser.parse_args(["-o", "reports/"])
#     output_file = collect(output=args.output)
#     assert os.path.exists(output_file) and os.path.isfile(output_file)

#     args = parser.parse_args(["-o", "reports/truc/"])
#     output_file = collect(output=args.output)
#     assert os.path.exists(output_file) and os.path.isfile(output_file)

#     args = parser.parse_args(["-o", "reports/truc2/"])
#     output_file = collect(output=args.output)
#     assert os.path.exists(output_file) and os.path.isfile(output_file)

#     args = parser.parse_args(["-o", "reports/test.json"])
#     output_file = collect(output=args.output)
#     assert os.path.exists(output_file) and os.path.isfile(output_file)

#     args = parser.parse_args(["-o", "reports/truc/test.json"])
#     output_file = collect(output=args.output)
#     assert os.path.exists(output_file) and os.path.isfile(output_file)

#     args = parser.parse_args(["-o", "reports.json"])
#     output_file = collect(output=args.output)
#     assert os.path.exists(output_file) and os.path.isfile(output_file)


if __name__ == "__main__":
    main()
    # launch_after_preload(main)  # TODO change that to settings.py
