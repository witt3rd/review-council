"""Formats counts as text."""

from tally import core


def report(text, top=0):
    """The report for `text`: lines, words, characters and, if `top` > 0, the
    top words."""
    out = [
        f"lines: {core.count_lines(text)}",
        f"words: {core.count_words(text)}",
        f"chars: {core.count_chars(text)}",
    ]
    for word, count in core.top_words(text, top):
        out.append(f"  {word}: {count}")
    return "\n".join(out)
