from CodeScalpel.scalpel import Scalpel
file_path = "ANNOTATED_EXAMPLE.md"
with open(file_path, "r") as input_file:
    text = input_file.read()
    summary = Scalpel.process_string(text)
    print(summary)
