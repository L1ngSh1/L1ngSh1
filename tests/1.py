"""Executable arithmetic fixture for the collaborative test workflow.

Run directly: python3 tests/1.py -v
Discovery entry: tests/test_collaborative_workflow.py
The numeric filename is retained for compatibility with the existing file.
"""

import unittest


def add(a: int, b: int) -> int:
    """Return the exact sum of integers; reject booleans and other types."""
    if not isinstance(a, int) or isinstance(a, bool):
        raise TypeError("a must be an integer (not bool)")
    if not isinstance(b, int) or isinstance(b, bool):
        raise TypeError("b must be an integer (not bool)")
    return a + b


class AddTests(unittest.TestCase):
    def test_positive_integers(self):
        self.assertEqual(add(2, 3), 5)

    def test_negative_integers(self):
        self.assertEqual(add(-2, -3), -5)

    def test_zero_identity(self):
        for value in (0, 7, -7):
            with self.subTest(value=value):
                self.assertEqual(add(value, 0), value)
                self.assertEqual(add(0, value), value)

    def test_mixed_signs(self):
        self.assertEqual(add(7, -3), 4)
        self.assertEqual(add(-7, 3), -4)

    def test_large_integers_remain_exact(self):
        self.assertEqual(add(2**63 - 1, 1), 2**63)
        self.assertEqual(add(-(2**63), -1), -(2**63) - 1)
        self.assertEqual(add(10**100, 1), 10**100 + 1)

    def test_opposites_cancel(self):
        for value in (1, -1, 10**100):
            with self.subTest(value=value):
                self.assertEqual(add(value, -value), 0)


if __name__ == "__main__":
    unittest.main()
