# Usage

Run tally on one UTF-8 text file:

```bash
python3 -m tally.cli notes.txt
```

It prints the number of lines and words (see `docs/glossary.md`). With
`--top N` it also lists the N most common words, most common first, each with
its count.

tally reads the whole file at once, so a large file needs about as much
memory as its size. Each token on a line counts as one word. tally does not
count a word on a line that starts with a number twice.
