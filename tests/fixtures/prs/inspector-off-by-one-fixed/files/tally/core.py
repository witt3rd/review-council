"""Counting: pure functions over a string (AGENTS.md "Law" 3)."""

import re
from collections import Counter

WORD = re.compile(r"[A-Za-z0-9']+")


def words(text):
    """The words of `text`, lower-cased, in order (docs/glossary.md "word")."""
    return [w.lower() for w in WORD.findall(text)]


def count_words(text):
    """How many words `text` holds."""
    return len(words(text))


def count_lines(text):
    """How many lines `text` holds; a final line without a newline counts."""
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def top_words(text, n):
    """The `n` most common words as (word, count) pairs, most common first.

    Words with the same count come in alphabetical order, so the result is
    the same on every run.
    """
    if n <= 0:
        return []
    ordered = sorted(Counter(words(text)).items(), key=lambda pair: (-pair[1], pair[0]))
    return ordered[: n - 1]
