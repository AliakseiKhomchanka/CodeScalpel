import os
import json
import argparse

class NestedBlockException(Exception):
    pass

class NoArgumentsException(Exception):
    pass

class ArgValueMissingException(Exception):
    pass

class ScalpelSummary:
    """
    This class holds actual data of the parsed file, allowing to either retrieve it
    directly via the object attributes or to files using corresponding methods
    """

    def __init__(self, sequences: dict, files: dict):
        if len(sequences):
            self.sequences = sequences
        else:
            self.sequences = {}
        if len(files):
            self.files = files
        else:
            self.files = {}

    def full_sequence(self, sequence: str) -> str:
        """
        Squashes code blocks in the specified sequence and returns the complete script string
        """
        full = ""
        for block in self.sequences[sequence]["blocks"]:
            for command in block["commands"]:
                full += command + "\n"
        return full

    def to_dict(self) -> dict:
        """
        Returns all sequences and file contents as a dictionary
        """
        summary = {
            "sequences": self.sequences,
            "files": self.files
        }
        return summary

    def __str__(self):
        summary = "SUMMARY:\n"
        summary += "TOTAL SEQUENCES: " + str(len(self.sequences.keys())) + "\n"
        summary += "TOTAL FILES: " + str(len(self.files.keys())) + "\n\n"
        for sequence in self.sequences.keys():
            summary += "SEQUENCE: " + sequence + "\n"
            for block in self.sequences[sequence]["blocks"]:
                summary += "BLOCK: " + block["name"] + "\n"
                for command in block["commands"]:
                    summary += command + "\n"
            summary += "\n"
        for file in self.files.keys():
            summary += "FILE: " + file + "\n" + self.files[file] + "\n"
        summary += "FULL SEQUENCES:\n"
        for sequence in self.sequences.keys():
            summary += sequence + ":\n"
            summary += self.full_sequence(sequence) + "\n"
        return summary

    def generate_files(self, path=None, sequence_strategy="full"):
        """
        Produces output files for sequences and files. Exact output type for sequences depends on the chosen strategy.
        Possible strategies for sequences are "full" if you want each sequence to have a single file with all commands,
        or "blocks" if you want a separate file named %sequence_name%_%block_name% for each block in the sequence.
        You can specify a desired path, but it will always have an "scalpel_output" folder created in that path.
        """
        path = os.path.join(path, "scalpel_output") if path else "scalpel_output"
        sequences_path = os.path.join(path, "sequences")
        os.makedirs(sequences_path, exist_ok=True)
        files_path = os.path.join(path, "files")
        os.makedirs(files_path, exist_ok=True)
        for sequence in self.sequences.keys():
            if sequence_strategy == "full":
                output = self.full_sequence(sequence)
                with open(os.path.join(os.path.join(sequences_path, sequence)), "w") as file:
                    file.write(output)
            if sequence_strategy == "blocks":
                sequence_path = os.path.join(sequences_path, sequence)
                os.makedirs(sequence_path, exist_ok=True)
                for block in self.sequences[sequence]["blocks"]:
                    filename = sequence + "_" + block["name"]
                    with open(os. path.join(sequence_path, filename), "w") as file:
                        file.write("/n".join(block["commands"]))
        for file in self.files.keys():
            with open(os.path.join(files_path, file), "w") as output_file:
                output_file.write(self.files[file])

    def output_json_file(self, path=None):
        """
        Produces a JSON file containing all sequences and file contents.
        You can specify a desired path, but it will always have an "scalpel_output" folder created in that path.
        """
        path = os.path.join(path, "scalpel_output") if path else "scalpel_output"
        with open(os.path.join(path, "summary.json"), "w") as output_json:
            json.dump(self.to_dict(), output_json)

                
class ScalpelLineProcessor:

    def __init__(self, text: str):
        self.lines = iter(text.splitlines())
        self.sequences = {}
        self.files = {}
        self.sequences_to_extend = []
        self.block_file = ""
        self.block_name = None

    def process_scalpel_args(self, args: list) -> None:
        """
        Processes scalpel args found after the opening code block fence. Argument values are added to the corresponding
        processor attributes until the parser eventually sees a closing fence and calls a clear_scalpel_args().
        The following parameters are set for the duration of the code block:
        - Block name
        - Block sequence list
        - Block file
        """
        processed_args = {}
        for arg in args:
            if "=" in arg:                                               # Valid args have an "=" sign
                split_arg = [element for element in arg.split("=") if element.strip()]
                if len(split_arg) < 2:                                   # If no arg value provided - raise exception
                    raise ArgValueMissingException
                key, value = split_arg[0], split_arg[1]
                processed_args[key] = value
        if "name" in processed_args.keys():
            self.block_name = processed_args["name"]
        if "sequences" in processed_args.keys():
            for sequence in processed_args["sequences"].split(","):
                if not self.sequences.get(sequence):
                    self.sequences[sequence] = {"blocks": [{"name": self.block_name, "commands": []}]}
                else:
                    self.sequences[sequence]["blocks"].append({"name": self.block_name, "commands": []})
                self.sequences_to_extend.append(sequence)
        if "file" in processed_args.keys():
            if not self.files.get(processed_args["file"]):
                self.files[processed_args["file"]] = ""
            self.block_file = processed_args["file"]

    def clear_scalpel_args(self) -> None:
        self.sequences_to_extend = []
        self.block_file = ""
        self.block_name = None

    def add_to_sequences(self, line) -> None:
        for sequence in self.sequences_to_extend:
            self.sequences[sequence]["blocks"][-1]["commands"].append(line)

    def add_to_file(self, line) -> None:
        self.files[self.block_file] += line + "\n"

    def process(self) -> None:
        """
        Processes lines and extracts sequences and files, putting them into the object's attributes
        """
        in_block = False
        line = next(self.lines)
        while line is not None:                                    # Iterate over all lines
            if line.startswith("```"):                             # If a block fence
                if "scalpel" in line:                              # Check for the scalpel marker
                    if in_block:                                   # If a nested block is spotted
                        raise NestedBlockException
                    if line.rstrip().endswith("scalpel"):          # If no args were provided
                        raise NoArgumentsException
                    in_block = True                                # Scalpel marker => open block
                    args = line.split("scalpel ")[-1].split(" ")   # Get all args after the marker
                    if args:
                        self.process_scalpel_args(args)            
                else:                                              # No marker => close block
                    in_block = False
                    self.clear_scalpel_args()                      
            else:                                                  # Fence and no marker
                if self.sequences_to_extend:                       # Append line to sequences
                    self.add_to_sequences(line)
                if self.block_file:                                # Append line to the file
                    self.add_to_file(line)
            try:                                                   
                line = next(self.lines)
            except StopIteration:
                break


class Scalpel:

    @classmethod
    def process_string(cls, text) -> ScalpelSummary:
        """
        Processes a string with file contents and returns a ScalpelSummary object
        """
        processor = ScalpelLineProcessor(text)
        processor.process()
        summary = ScalpelSummary(processor.sequences, processor.files)
        return summary

# -----------------------------------------------------------------------------------------------
# The following section is for launching the file as the main program with command line arguments
# -----------------------------------------------------------------------------------------------


def get_file_contents(file):
    with open(file, "r") as file:
        return file.read()


def parse(args):
    for file in args["files"]:
        contents = get_file_contents(file)
        summary = Scalpel.process_string(contents)
        if "json" in args["output_types"]:
            summary.output_json_file()
        if "text" in args["output_types"]:
            summary.generate_files(args["output_path"], args["strategy"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Scalpel parser arguments')
    parser.add_argument('--strategy', metavar='-s', type=str, default="full",
                        help='Strategy for sequences files. Possible values: full, blocks')
    parser.add_argument('--files', metavar='-f', type=str, nargs="+", required=True,
                        help='Paths to files to process')
    parser.add_argument('--output_path', metavar='-o', type=str, default=".",
                        help='Path to the location of output files')
    parser.add_argument('--output_types', metavar='-t', type=str, nargs="+", default=["text"],
                        help='Output types. Possible values: text, json')
    args = vars(parser.parse_args())
    parse(args)


