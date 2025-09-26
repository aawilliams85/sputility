import glob
import os
import unittest

from sputility import *

# Shared paths
LOCAL_BASE_PATH = os.path.abspath(os.path.dirname(__file__))
LOCAL_INPUT_PATH = os.path.join(LOCAL_BASE_PATH, 'input_files')
LOCAL_OUTPUT_PATH = os.path.join(LOCAL_BASE_PATH, 'output_files')

LOCAL_INPUT_AAOBJECT_PATH = os.path.join(LOCAL_INPUT_PATH, 'aaobject')
LOCAL_INPUT_AAPKG_PATH = os.path.join(LOCAL_INPUT_PATH, 'aapkg')
LOCAL_OUTPUT_AAOBJECT_PATH = os.path.join(LOCAL_OUTPUT_PATH, 'aaobject')
LOCAL_OUTPUT_AAPKG_PATH = os.path.join(LOCAL_OUTPUT_PATH, 'aapkg')

class sputility_tests(unittest.TestCase):
    def setUp(self):
        pass

    def test_aapkg_to_folder(self):
        print('')
        for file in glob.glob(os.path.join(LOCAL_INPUT_AAPKG_PATH, '*.aaPKG')):
            aapkg.archive_to_disk(
                file_path=file,
                output_path=LOCAL_OUTPUT_AAPKG_PATH
            )

    def test_aaobject_to_folder(self):
        print('')
        for file in glob.glob(os.path.join(LOCAL_INPUT_AAOBJECT_PATH, '*.txt')):
            aaobject.explode_aaobject(
                input=file,
                output_path=LOCAL_OUTPUT_AAOBJECT_PATH
            )

    def tearDown(self):
        pass