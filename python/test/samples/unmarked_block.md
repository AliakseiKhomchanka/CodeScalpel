# code-snippet-testing

Here's one code snippet for both sequences:

```sh scalpel sequences=first.sh,second.sh name=list_files
ls -a
```

```json scalpel file=example.json
{
  "first":  "this",
  "second": "that"
}
```

```sh
echo "This block will be ignored by scalpel"
```

Here's a code snippet for only the first sequence:

```sh scalpel sequences=first.sh name=first_echo
echo "I'm in the first sequence"
echo "I'm still in the first sequence"
echo "Even I am in the first sequence"
``` 

Here's a code snippet for only the second sequence:

```sh scalpel sequences=second.sh name=second_echo
echo "I'm in the second sequence"
```