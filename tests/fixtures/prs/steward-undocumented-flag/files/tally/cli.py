"""The command line: reads the file and prints the report."""

import argparse
import json
import sys

from tally import core
from tally.report import report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tally", description="Count the words and lines in a text file.")
    parser.add_argument("file", help="the text file to count")
    parser.add_argument("--top", type=int, default=0, metavar="N", help="also list the N most common words")
    parser.add_argument("--json", action="store_true", help="print the counts as one JSON object")
    args = parser.parse_args(argv)
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    if args.json:
        print(json.dumps({"lines": core.count_lines(text), "words": core.count_words(text)}))
    else:
        print(report(text, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
