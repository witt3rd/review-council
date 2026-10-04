# AGENTS.md — tally

tally counts the words and lines in a text file. It is a fixture for the
review council's evals: small on purpose, with written law a reviewer can
cite.

## Law

1. **Documented flags.** Every command-line flag is listed in `README.md`
   §Flags, in the same PR that adds, changes or removes it.
2. **Changelog.** Every change of behaviour adds a line to `CHANGELOG.md`
   under `## Unreleased`, in the same PR.
3. **Pure core.** `tally/core.py` does no I/O (no files, network, clock,
   environment or printing) and imports only `re` and `collections`.
   Reading files and printing belong to `tally/cli.py`.
4. **Tests.** Tests live in `tests/` and use `unittest`. Every change of
   behaviour in `tally/core.py` comes with a test that fails without it.

## Layout

```text
tally/core.py     counting: pure functions over a string
tally/report.py   formats counts as text
tally/cli.py      the command line: reads the file, prints the report
tests/            unittest tests
docs/glossary.md  the terms docs use, one meaning each
docs/usage.md     how to run it
```

## Commands

```bash
python3 -m unittest discover -s tests
python3 -m tally.cli FILE
```
