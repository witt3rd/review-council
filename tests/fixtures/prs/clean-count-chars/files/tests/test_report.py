import unittest

from tally.report import report


class ReportTest(unittest.TestCase):
    def test_report_lists_top_words(self):
        self.assertEqual(report("b a b\n", top=1), "lines: 1\nwords: 3\nchars: 6\n  b: 2")


if __name__ == "__main__":
    unittest.main()
