from CodeScalpel.scalpel import ScalpelLineProcessor
import unittest
# from unittest import mock
import os
import json
import sys

from CodeScalpel.scalpel import Scalpel, NestedBlockException, NoArgumentsException


def get_file_contents(file):
    with open(os.path.join("test", "samples", file), "r") as test_file:
        return test_file.read()


class TestParser(unittest.TestCase):

    def test_correct_file(self):
        file_contents = get_file_contents("no_errors.md")
        expected_summary = json.loads(get_file_contents("no_errors_summary.json"))
        summary = Scalpel.process_string(file_contents).to_dict()
        assert summary == expected_summary

    def test_nested_block_exception(self):
        file_contents = get_file_contents("nested_block.md")
        self.assertRaises(NestedBlockException, Scalpel.process_string, file_contents)

    def test_error_no_args_provided(self):
        file_contents = get_file_contents("no_block_args.md")
        self.assertRaises(NoArgumentsException, Scalpel.process_string, file_contents)

    def test_ignore_unmarked_blocks(self):
        file_contents = get_file_contents("unmarked_block.md")
        expected_summary = json.loads(get_file_contents("unmarked_block_summary.json"))
        summary = Scalpel.process_string(file_contents).to_dict()
        assert summary == expected_summary
