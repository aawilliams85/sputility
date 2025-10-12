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
LOCAL_OUTPUT_AAPKG_DECOOMPRESSED_PATH = os.path.join(LOCAL_OUTPUT_PATH, 'aapkg_decompressed')
LOCAL_OUTPUT_AAPKG_DESERIALIZED_PATH = os.path.join(LOCAL_OUTPUT_PATH, 'aapkg_deserialized')

class sputility_tests(unittest.TestCase):
    def setUp(self):
        pass

    def test_decompress_package(self):
        print('')
        for file in glob.glob(os.path.join(LOCAL_INPUT_AAPKG_PATH, '*.aaPKG')):
            spu = SPUtility()
            resp = spu.decompress_package(
                input_path=file,
                output_path=LOCAL_OUTPUT_AAPKG_DECOOMPRESSED_PATH,
                progress=None
            )
            pprint.pprint(resp)

    def test_deserialize_package(self):
        print('')
        for file in glob.glob(os.path.join(LOCAL_INPUT_AAPKG_PATH, '*.aaPKG')):
            spu = SPUtility()
            resp = spu.deserialize_package(
                input_path=file,
                output_path=LOCAL_OUTPUT_AAPKG_DESERIALIZED_PATH,
                progress=None
            )

    def test_deserialize_object(self):
        print('')
        for file in glob.glob(os.path.join(LOCAL_INPUT_AAOBJECT_PATH, '*.txt')):
            spu = SPUtility()
            print(file)
            resp = spu.deserialize_object(
                input_path=file,
                output_path=LOCAL_OUTPUT_AAOBJECT_PATH,
                progress=None
            )
            print(f'Parsed {resp.offset:0X} of {resp.size:0X} bytes, {(100.0 * resp.offset / resp.size):.1f}%')
            #pprint.pprint(resp.header)
            #print(f'{len(resp.extensions)} extensions')
            #for ext in resp.extensions:
            #    print(f'Extension {ext.instance_id:0X} {ext.extension_name} has {len(ext.attributes)} attributes.')
            #    #print(f'{len(section.attributes)} attrs')
            #    #print(f'Primitive name: {section.primitive_name}, Count: {len(section.attributes)}')
            #    #for attr in section.attributes:
            #    #    print(f'Attribute ID: {attr.id}')
            #    #for attr in section.attributes:
            #    #    print(attr.id)
            #    #pprint.pprint(section)
            #    pass

    def tearDown(self):
        pass