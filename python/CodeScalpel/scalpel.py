import os
import pathlib
import json

class NestedBlockException(Exception):
    pass

class NoArgumentsException(Exception):
    pass

class ScalpelSummary:

    def __init__(self, sequences: dict, files: dict):
        if len(sequences):
            self.sequences = sequences
        else:
            self.sequences = {}
        if len(files):
            self.files = files
        else:
            self.files = {}

    def full_sequence(self, sequence):
        full = ""
        for block in self.sequences[sequence]["blocks"]:
            for command in block["commands"]:
                full += command + "\n"
        return full

    def to_dict(self):
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
        path = os.path.join(path, "scalpel_output") if path else "scalpel_output"
        sequences_path = os.path.join(path, "sequences")
        os.makedirs(sequences_path, exist_ok=True)
        files_path = os.path.join(path, "files")
        os.makedirs(files_path, exist_ok=True)
        for sequence in self.sequences.keys():
            if sequence_strategy == "full":
                output = self.full_sequence(sequence)
                with open(os.path.join(os.path.join(sequences_path, sequence)), "w") as sequence_file:
                    sequence_file.write(output)
            if sequence_strategy == "blocks":
                sequence_path = os.path.join(sequences_path, sequence)
                os.makedirs(sequence_path, exist_ok=True)
                for block in self.sequences[sequence]["blocks"]:
                    filename = sequence + "_" + block["name"]
                    with open(os. path.join(sequence_path, filename), "w") as block_file:
                        block_file.write("/n".join(block["commands"]))
        for file in self.files.keys():
            with open(os.path.join(files_path, file), "w") as output_file:
                output_file.write(self.files[file])

    def output_json_file(self, path=None):
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

    def get_sequences(self):
        return self.sequences

    def get_files(self):
        return self.files

    def process_scalpel_args(self, args: list):
        processed_args = {}
        for arg in args:
            key, value = None, None
            if "=" in arg:
                arg = arg.split("=")
                key, value = arg[0], arg[1]
            if key and value:
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

    def clear_scalpel_args(self):
        self.sequences_to_extend = []
        self.block_file = ""
        self.block_name = None

    def add_to_sequences(self, line):
        for sequence in self.sequences_to_extend:
            self.sequences[sequence]["blocks"][-1]["commands"].append(line)

    def add_to_file(self, line):
        self.files[self.block_file] += line + "\n"

    def process(self):
        """
        Processes lines and extracts sequences and files
        """
        in_block = False
        line = next(self.lines)
        while line is not None:                                         # While there are lines to process
            if line.startswith("```"):                                  # If a code block is spotted
                if "scalpel" in line:                                   # Check for the scalpel marker
                    if in_block:                                        # Raise exception if a block is already open
                        raise NestedBlockException
                    if line.rstrip().endswith("scalpel"):               # Raise exception if no arguments were provided
                        raise NoArgumentsException
                    in_block = True                                     # Scalpel marker => open block
                    args = line.split("scalpel ")[-1].split(" ")        # Get all args after the marker
                    if args:
                        self.process_scalpel_args(args)                 # If there are args - process them
                else:                                                   # Back ticks without marker => close block
                    in_block = False
                    self.clear_scalpel_args()                           # Clear current sequence and file names
            else:                                                       # No back ticks => treat as a normal line
                if self.sequences_to_extend:                            # Append to sequences where needed
                    self.add_to_sequences(line)
                if self.block_file:                                     # Append to the file where needed
                    self.add_to_file(line)
            try:                                                        # Go to the next line, if there is one
                line = next(self.lines)
            except StopIteration:
                break


class Scalpel:

    @classmethod
    def process_string(cls, text):
        processor = ScalpelLineProcessor(text)
        processor.process()
        summary = ScalpelSummary(processor.get_sequences(), processor.get_files())
        return summary
