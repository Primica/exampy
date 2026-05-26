from __future__ import annotations

import unittest

from shell.parser import parse_line


class ParseLineTests(unittest.TestCase):
    def test_returns_empty_list_for_blank_input(self) -> None:
        self.assertEqual(parse_line("   \t  "), [])

    def test_splits_simple_command(self) -> None:
        self.assertEqual(parse_line("campaign list"), ["campaign", "list"])

    def test_respects_quotes(self) -> None:
        self.assertEqual(
            parse_line('quest create "First quest" "Go north." open "World"'),
            ["quest", "create", "First quest", "Go north.", "open", "World"],
        )

    def test_raises_on_invalid_quotes(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            parse_line('quest create "unterminated')
        self.assertIn("Invalid quotes or escape sequence", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
