"""
Test module for gramolang package
"""

import unittest
from pathlib import Path

from gramolang.common import set_openai_api_key
from gramolang.sheet import complete
from gramolang.auto import pool_files

API_KEY_FILE = Path.home() / '.mz/openai-api-key-uqam'
RESS_PATH = Path(__file__).parent / 'ress'


class CaseSheet(unittest.TestCase):

    def setUp(self) -> None:

        # Set OpenAI API Key
        set_openai_api_key(API_KEY_FILE)

    @unittest.skip
    def test_sheet_completion(self):
        complete(
            workbook_path=RESS_PATH / 'test.xlsx',
            api_key_file=API_KEY_FILE,
            new_workbook_path=RESS_PATH / 'test_completed.xlsx')

    #@unittest.skip
    def test_sheet_completion_error(self):
        complete(
            workbook_path=RESS_PATH / 'test.xlsx',
            new_workbook_path=RESS_PATH / 'test_completed.xlsx')

    @unittest.skip
    def test_pool(self):
        pool_files(root_dir=RESS_PATH / 'pool', api_key_file=API_KEY_FILE)
