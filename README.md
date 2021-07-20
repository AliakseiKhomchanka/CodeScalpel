# CodeScalpel

CodeScalpel (also referred to as simply Scalpel further down) is a tool for marking and extracting code snippets in .md files for further testing.

It uses a simple approach to marking executable code while allowing considerable flexibility in selecting and sorting code snippets.

## What is does

Scalpel allows extraction of code snippets that have been marked with certain markers that can be seen in the raw file but aren't actually rendered. 
An example of such markers is:
```
 ```sh scalpel sequence=first,second name=echoing_things
 echo "Echoing the first line"
 echo "Echoing the second line"
 ```
```
```
 ```JSON scalpel file=payload.json
 {
   "first": "one",
   "second": "two"
 }
 ```
```
As you can see, in addition to normal triple back ticks around the code block, there are annotations after opening the block. 
The first one, `shell`, is a language indicator, commonly seen on GitHub in README files. 
The word `scalpel` indicates that this block has been marked for processing by the parser. 
After that, several Scalpel-specific parameters follow.

### Scalpel parameters

####`sequences`

Sequences are an integral part of Scalpel. The idea is that each block can belong to one or more sequences. 
Sequences that a block belongs to are put into the `sequences` argument, separated with commas **without spaces**:

`sequences=first,second,third`

####`name`

Each code block can be given an individual name so that after parsing users could work with code blocks within each sequence separately.
You might want to do that when you don't want to test the sequence as a whole but would rather test them step by step:

`name=block_that_does_x`

####`file`

Some code blocks are not actual executable blocks, but rather just data, like JSON or YAML files. 
In that case, they can be marked as such in code block annotations as well:

`file=payload.json` 


### How the parser works

The parser checks all code blocks in a file one by one from top to bottom.
When it sees scalpel annotations - it checks whether the block belongs to some sequences or if it is a file.
If there are any matches - the current block is added to corresponding sequences (with its own block name, if provided).
If there are any files specified - their contents are also populated.

Code blocks without scalpel annotations are ignored.

### Example of a file with markings

Let's say you want to use environment variables. Define some variables first:
```sh scalpel sequences=exported,not_exported name=setting_vars
  FIRST=something
  SECOND=something_else
```

Then, if you want to use them in another process, you need to export them:
```sh scalpel sequences=exported name=export_vars
  export FIRST
  export SECOND
```

Now check the list of exported variables to see if it has been exported or not:
```sh scalpel sequences=exported,not_exported name=check_exports
  export -p | grep FIRST
  export -p | grep SECOND
```

You should see output if variables have been exported. Otherwise, there should be no output.
If there is no output, declare your powerlessness:
```sh scalpel sequences=not_exported name=give_up
  echo "I AM POWERLESS"
```

Also, here's a JSON file for your entertainment:
```json file=example.json
  {
    "first": "one",
    "second": "two"
  }
```

---
Now let's look at this same file in its raw form with invisible annotations:

````
Let's say you want to use environment variables. Define some variables first:
```sh scalpel sequences=exported,not_exported name=setting_vars
  FIRST=something
  SECOND=something_else
```

Then, if you want to use them in another process, you need to export them:
```sh scalpel sequences=exported name=export_vars
  export FIRST
  export SECOND
```

Now check the list of exported variables to see if it has been exported or not:
```sh scalpel sequences=exported,not_exported name=check_exports
  export -p | grep FIRST
  export -p | grep SECOND
```

You should see output if variables have been exported. Otherwise, there should be no output.
If there is no output, declare your powerlessness:
```sh scalpel sequences=not_exported name=give_up
  echo "I AM POWERLESS"
```

Also, here's a JSON file for your entertainment:
```json scalpel file=example.json
  {
    "first": "one",
    "second": "two"
  }
```
````

As you can see, the file is supposed to have two sequences, `exported`, where variables were exported 
and `not_exported`, where they haven't been exported and where the user admits defeat. 
All code blocks have individual names, specifying their purpose.
At the end of a file, there is also an example of a JSON file named `example.json`. 

Thus, after the parser runs on this file, it will generate two sequences and a file:

---
Sequence named `exported`:

1: Block named `setting_vars`
```
FIRST=something
SECOND=something_else
```
2: Block named `export_vars`
```
export FIRST
export SECOND
```
3: Block named `check_exports`
```
export -p | grep FIRST
export -p | grep SECOND
```
---
Sequence named `not_exported`:

1: Block named `setting_vars`
```
FIRST=something
SECOND=something_else
```
2: Block named `check_exports`
```
export -p | grep FIRST
export -p | grep SECOND
```
3: Block named `give_up`
```
echo "I AM POWERLESS"
```
---
File named `example.json`:
```
{
  "first": "one",
  "second": "two"
}
```

