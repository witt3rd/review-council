import unittest

from tally import core


class CoreTest(unittest.TestCase):
    def test_words_are_lower_cased_in_order(self):
        self.assertEqual(core.words("The cat, the HAT."), ["the", "cat", "the", "hat"])

    def test_count_lines_counts_a_final_line_without_newline(self):
        self.assertEqual(core.count_lines("a\nb"), 2)
        self.assertEqual(core.count_lines("a\nb\n"), 2)
        self.assertEqual(core.count_lines(""), 0)

    def test_count_chars_counts_newlines(self):
        self.assertEqual(core.count_chars("ab\nc\n"), 5)
        self.assertEqual(core.count_chars(""), 0)
        self.assertEqual(core.count_chars("é"), 1)

    def test_top_words(self):
        self.assertEqual(core.top_words("b a b c b a", 2), [("b", 3), ("a", 2)])
        self.assertEqual(core.top_words("a b", 0), [])


if __name__ == "__main__":
    unittest.main()
