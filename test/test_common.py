"""
Main test module

"""

import unittest
from pathlib import Path

from gramolang.common import (
    NAME_VALUE_SEPS, SPACE_SEP, parse_name_value,
    get_file_variable)


class MainCase(unittest.TestCase):

    def setUp(self) -> None: pass

    @unittest.skip
    def test_skip_example(self): pass

    def test_parse_name_value(self):
        """Test split_name_argument function"""

        # Basic cases
        for sep in NAME_VALUE_SEPS + (SPACE_SEP,):
            self.assertEqual(('name', 'arguments'), parse_name_value(f"name{sep}arguments"))
            self.assertEqual(('name', 'arguments'), parse_name_value(f"name {sep}arguments"))
            self.assertEqual(('name', 'arguments'), parse_name_value(f"name{sep} arguments"))
            self.assertEqual(('name', 'arguments'), parse_name_value(f"name {sep} arguments"))
            self.assertEqual(('name', 'arguments'), parse_name_value(f"name  {sep}   arguments"))
            self.assertEqual(('name', 'arguments'), parse_name_value(f" name{sep}arguments "))

        # Single element
        self.assertEqual((None, 'value'), parse_name_value(f"value"))
        self.assertEqual((None, 'value'), parse_name_value(f" value "))
        self.assertEqual((None, 'value'), parse_name_value(f"{SPACE_SEP}value{SPACE_SEP}"))

        self.assertEqual(('name', None), parse_name_value(f"name", single_name=True))
        self.assertEqual(('name', None), parse_name_value(f" name ", single_name=True))
        self.assertEqual(('name', None), parse_name_value(f"{SPACE_SEP}name{SPACE_SEP}", single_name=True))

        # Name only
        for sep in NAME_VALUE_SEPS:
            self.assertEqual(('name', None), parse_name_value(f"name{sep}"))
            self.assertEqual(('name', None), parse_name_value(f"name {sep}"))
            self.assertEqual(('name', None), parse_name_value(f"name{sep} "))
            self.assertEqual(('name', None), parse_name_value(f"name {sep} "))
            self.assertEqual(('name', None), parse_name_value(f" name {sep} "))

        # Value only
        for sep in NAME_VALUE_SEPS:
            self.assertEqual((None, 'arguments'), parse_name_value(f"{sep}arguments"))
            self.assertEqual((None, 'arguments'), parse_name_value(f" {sep}arguments"))
            self.assertEqual((None, 'arguments'), parse_name_value(f"{sep} arguments"))
            self.assertEqual((None, 'arguments'), parse_name_value(f" {sep} arguments"))

        # Multiple separators
        sep0 = NAME_VALUE_SEPS[0]
        sep1 = NAME_VALUE_SEPS[1]
        self.assertEqual(
            ('name', f'{sep1}arguments'),
            parse_name_value(f"name{sep0}{sep1}arguments"))
        self.assertEqual(
            ('name', f'{sep0}arguments'),
            parse_name_value(f"name{sep1}{sep0}arguments"))
        self.assertEqual(
            ('name', f'{sep0}{sep1}arguments'),
            parse_name_value(f"name{sep1}{sep0}{sep1}arguments"))
        self.assertEqual(
            ('name', f'{sep0}{sep1}arguments'),
            parse_name_value(f"name{sep1} {sep0}{sep1}arguments"))
        self.assertEqual(
            ('name', f'{sep0} {sep1}arguments'),
            parse_name_value(f"name{sep1}{sep0} {sep1}arguments"))

    @unittest.skip
    def test_get_file_variable(self):
        # TODO: Add tests for getting file variables for API keys
        pass
