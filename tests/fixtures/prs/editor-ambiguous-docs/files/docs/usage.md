# Usage

Run tally on one UTF-8 text file:

```bash
python3 -m tally.cli notes.txt
```

It prints the number of lines and words (see `docs/glossary.md`). With
`--top N` it also lists the N most common words, most common first, each with
its count.

Large files may take a while, and very large ones are not always counted
fully. Each token is counted once per line, so a word repeated on one line is
not counted twice unless it is not split by punctuation. `--top` does not
leave out words that are not rare unless N is small.
