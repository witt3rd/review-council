# Usage

Run tally on one UTF-8 text file:

```bash
python3 -m tally.cli notes.txt
```

It prints the number of lines, words and characters (see `docs/glossary.md`). With
`--top N` it also lists the N most common words, most common first, each with
its count.
