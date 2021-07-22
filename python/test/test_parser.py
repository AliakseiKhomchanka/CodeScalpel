import unittest
import os
import json

from CodeScalpel.scalpel import Scalpel, NestedBlockException, NoArgumentsException, ArgValueMissingException


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

    def test_no_args_provided_exception(self):
        file_contents = get_file_contents("no_block_args.md")
        self.assertRaises(NoArgumentsException, Scalpel.process_string, file_contents)

    def test_ignore_unmarked_blocks(self):
        file_contents = get_file_contents("unmarked_block.md")
        expected_summary = json.loads(get_file_contents("unmarked_block_summary.json"))
        summary = Scalpel.process_string(file_contents).to_dict()
        assert summary == expected_summary

    def test_missing_arg_value_exception(self):
        file_contents = get_file_contents("no_arg_value.md")
        self.assertRaises(ArgValueMissingException, Scalpel.process_string, file_contents)
