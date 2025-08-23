import os
import unittest

from sputility import *

# Shared paths
LOCAL_BASE_PATH = os.path.abspath(os.path.dirname(__file__))
LOCAL_INPUT_PATH = os.path.join(LOCAL_BASE_PATH, 'input_files')
LOCAL_OUTPUT_PATH = os.path.join(LOCAL_BASE_PATH, 'output_files')
LOCAL_INPUT_AAPKG_PATH = os.path.join(LOCAL_INPUT_PATH, 'aapkg')
LOCAL_OUTPUT_AAPKG_PATH = os.path.join(LOCAL_OUTPUT_PATH, 'aapkg')

STANDALONE_AAPKG_FILES = [
    os.path.join(LOCAL_INPUT_AAPKG_PATH, '$TEMPLATE_NAME_01_A.aaPKG')
]

class sputility_tests(unittest.TestCase):
    def setUp(self):
        pass

    def test_aapkg_to_folder(self):
        print('')
        for file in STANDALONE_AAPKG_FILES:
            sputility.archive_to_disk(
                file_path=file,
                output_path=LOCAL_OUTPUT_AAPKG_PATH
            )

    def tearDown(self):
        pass