import glob
import os
import pprint
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
            spu = SPUtility()
            resp = spu.decompress_package(
                input_path=file,
                output_path=LOCAL_OUTPUT_AAPKG_PATH,
                progress=None
            )
            pprint.pprint(resp)

    def test_aaobject_to_folder(self):
        print('')
        for file in glob.glob(os.path.join(LOCAL_INPUT_AAOBJECT_PATH, '*.txt')):
            spu = SPUtility()
            resp = spu.explode_object(
                input_path=file,
                output_path=LOCAL_OUTPUT_AAOBJECT_PATH,
                progress=None
            )
            print(f'Parsed {resp.offset:0X} of {resp.size:0X} bytes')
            #pprint.pprint(resp.header)
            for section in resp.content.extensions:
                #print(f'Primitive name: {section.primitive_name}, Count: {len(section.attributes)}')
                #for attr in section.attributes:
                #    print(f'Attribute ID: {attr.id}')
                #for attr in section.attributes:
                #    print(attr.id)
                #pprint.pprint(section)
                pass

    def tearDown(self):
        pass