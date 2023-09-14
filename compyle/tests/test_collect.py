import argparse
import os
import pathlib
import sys
from typing import Any, Dict, Sequence
from unittest import TestCase, main, mock, skip

from compyle.actions import collect


class TestParser(TestCase):
    maxDiff = None

    def setUp(self):
        os.environ = {}
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    def tearDown(self):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class TestCollect(TestParser):
    output_files = [
        "file.json",
        "./file.json",
        "./dir/file.json",
        "dir/file.json",
        "/dir1/dir2/file.json",
        "./",
        "",
        ".",
        "/dir1/dir2/",
    ]

    def parse_args(self, args: Sequence[str]) -> argparse.Namespace:
        return collect.get_parser(argparse.ArgumentParser().add_subparsers(required=True)).parse_args(args)

    def get_vars(self, args: Sequence[str]) -> Dict[str, Any]:
        return vars(self.parse_args(args))

    def test_parser_output_arg(self):
        for output_file in self.output_files:
            args: Dict[str, Any] = self.get_vars(["-out", output_file])

            self.assertIn("output", args, "the output argument should be present in the namespace")
            self.assertEqual(
                args["output"], pathlib.Path(output_file), "the output argument should be equal to the normalized path"
            )

    def test_parser_output_alias(self):
        args: Dict[str, Any] = self.get_vars(["-out", self.output_files[0]])

        self.assertIn("output", args, "the output argument should be present in the namespace")
        self.assertEqual(
            args["output"],
            pathlib.Path(self.output_files[0]),
            "the output argument should be equal to the normalized path",
        )

    def test_parser_output_nargs_value(self):
        line: Sequence[str] = ["-out", *self.output_files[:2]]

        with self.assertRaises(SystemExit, msg=f"error: unrecognized arguments: {line[-1]}") as cm:
            self.parse_args(line)
        self.assertEqual(
            cm.exception.code, 2, "the parser should exit with code 2 when an unrecognized argument is provided"
        )

    def test_parser_out_nargs_key(self):
        line: Sequence[str] = ["-out", "file.json", "-out", "file2.json"]
        args: Dict[str, Any] = self.get_vars(line)

        self.assertIn("output", args, "the output argument should be present in the namespace")
        self.assertEqual(
            args["output"], pathlib.Path(line[-1]), "the output argument should be equal to the last value provided"
        )

    def test_parser_output_const(self):
        args: Dict[str, Any] = self.get_vars(["-out"])

        self.assertIn("output", args, "the output argument should be present in the namespace")
        self.assertEqual(
            args["output"],
            pathlib.Path(collect.DEFAULT_REPORT_FOLDER),
            "the output argument should be equal to the default value",
        )

    def test_parser_output_required(self):
        with self.assertRaises(SystemExit, msg="error: the following arguments are required: -out/--output") as cm:
            argparse.Namespace = self.parse_args([])
        self.assertEqual(
            cm.exception.code, 2, "the parser should exit with code 2 when an unrecognized argument is provided"
        )

    def test_parser_output_suppress(self):
        os.environ["MONGO_DB_URI"] = "mongodb://localhost:27017"
        args: Dict[str, Any] = self.get_vars([])

        self.assertNotIn(
            "output", args, "the output argument should not be present in the namespace because not required"
        )

    def test_parser_db_ignored_with_output(self):
        os.environ["MONGO_DB_URI"] = "mongodb://localhost:27017"
        args: Dict[str, Any] = self.get_vars(["-out", self.output_files[0]])

        self.assertIn("output", args, "the output argument should be present in the namespace")
        self.assertEqual(
            args["output"],
            pathlib.Path(self.output_files[0]),
            "the output argument should be equal to the normalized path",
        )

    @skip("TODO: mock the twitch api")
    @mock.patch("compyle.services.databases.mongo.MongoDB")
    @mock.patch("compyle.services.controllers.twitch.TwitchAPI")
    def test_x(self, mock_twitch_api: mock.MagicMock):
        mock_twitch_api.return_value = mock.MagicMock()
        mock_twitch_api.return_value.get_game_id.return_value = mock.MagicMock()
        mock_twitch_api.return_value.get_clips.return_value = mock.MagicMock()

        kwargs: Dict[str, Any] = dict(self.parse_args(["-out", self.output_files[0]])._get_kwargs())
        kwargs.pop("func")(**kwargs)


if __name__ == "__main__":
    main()
