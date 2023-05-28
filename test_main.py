import argparse
import logging
from os import getenv
import pathlib
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
    with open("pyproject.toml", "r", encoding="utf-8") as file:
        section: Dict[str, Any] = toml.load(file)["tool"]["poetry"]
        name, description, version = [keyword for keyword in section if keyword in ["name", "description", "version"]]

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

    # creates the subparser for the several commands
    subparser: argparse._SubParsersAction = parser.add_subparsers(
        dest="action", help="select the action to perform", required=True
    )

    # the parser for the 'collect' action
    parser_collect: argparse.ArgumentParser = subparser.add_parser(
        "collect", aliases=["c"], description="TODO", formatter_class=argparse.RawTextHelpFormatter
    )  # TODO description
    parser_collect.set_defaults(func=collect.collect)
    # g = parser_collect.add_mutually_exclusive_group(required=True)
    # g1 = g.add_argument_group()
    # g1.add_argument()
    # g2 = g.add_argument_group()
    parser_collect.add_argument(
        "-out",
        "--output",
        type=pathlib.Path,
        metavar="FILE | DIRECTORY",
        help="""specifiy the output path where to store the report:
    if a file is specified, all path elements including the file iteself will be created if needed
    if a directory is specified, the report will be stored in a file named with the current
    if none is specified, the report will be stored in the database""",
        default=argparse.SUPPRESS,  # TODO remove me DEFAULT_REPORT_FOLDER
    )
    import sys

    print(sys.getdefaultencoding())
    # the parser for the 'edit' action
    parser_edit: argparse.ArgumentParser = subparser.add_parser("edit", aliases=["e"])
    parser_edit.set_defaults(func=None)  # TODO set the function
    parser_edit.add_argument(
        "-in",
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
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
    parser_publish: argparse.ArgumentParser = subparser.add_parser("publish", aliases=["p"])
    parser_publish.set_defaults(func=None)  # TODO set the function
    parser_publish.add_argument(
        "-in",
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        metavar="FILE | DIRECTORY",
        help="specifiy the input path where to retrieve the video data from",
        default=DEFAULT_VIDEO_FOLDER,
    )
    # TODO validate must exists

    # parses the arguments present in the command line
    kwargs: Dict[str, Any] = {key: value for key, value in parser.parse_args()._get_kwargs()}

    # sets the logging level
    logging.basicConfig(level=levels[min(kwargs.pop("verbose"), len(levels) - 1)])

    exit(0)

    kwargs.pop("func")(**kwargs)

    return args.func(**kwargs)


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
