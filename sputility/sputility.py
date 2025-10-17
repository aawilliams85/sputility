from collections.abc import Callable
import os
from typing import Optional
from warnings import warn

from . import obj
from . import pkg

class SPUtility(object):
    def __init__(self):
        pass

    def decompress_package(
        self,
        input_path: str,
        output_path: str,
        progress: Optional[Callable[[str, str, int, int], None]] = None, 
    ) -> pkg.types.AaManifest:
        if not(os.path.isfile(input_path)): raise FileNotFoundError(f'Input file specified ({input_path}) does not exist.')
        if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)
        result = pkg.decompress.aapkg_to_folder(input_path=input_path, output_path=output_path)
        return result

    def deserialize_package(
        self,
        input_path: str,
        output_path: str,
        progress: Optional[Callable[[str, str, int, int], None]] = None, 
    ) -> list[obj.types.AaObject]:
        if not(os.path.isfile(input_path)): raise FileNotFoundError(f'Input file specified ({input_path}) does not exist.')

        result = []

        aapkg_name = os.path.splitext(os.path.basename(input_path))[0]
        aapkg_path = os.path.join(output_path, aapkg_name)
        if not(os.path.exists(aapkg_path)): os.makedirs(aapkg_path, exist_ok=True)
        (manifest, streams) = pkg.decompress.aapkg_to_memory(input_path=input_path)

        def _get_stream(name: str, streams: list[pkg.types.AaArchive]) -> pkg.types.AaArchive:
            return next((stream for stream in streams if stream.name == name), None)

        def _get_stream_filename(tag_name: str, file_name: str, protected: bool) -> str:
           if protected:
               return f'{tag_name}.txt'
           else:
               return file_name

        def _recurse(template: pkg.types.AaManifestTemplate, result: list[obj.types.AaObject]):
            #print(template.tag_name)
            result.append(obj.deserialize.aaobject_to_folder(_get_stream(_get_stream_filename(template.tag_name, template.file_name, template.is_protected), streams).data, output_path=aapkg_path))
            for child in template.derived_templates:
                _recurse(template=child, result=result)

            for child in template.derived_instances:
                #print(child.file_name)
                result.append(obj.deserialize.aaobject_to_folder(_get_stream(child.file_name, streams).data, output_path=aapkg_path))

        for template in manifest.templates:
            _recurse(template=template, result=result)

        return result

    def deserialize_object(
        self,
        input_path: str,
        output_path: str,
        progress: Optional[Callable[[str, str, int, int], None]] = None, 
    ) -> obj.types.AaObject:
        if not(os.path.isfile(input_path)): raise FileNotFoundError(f'Input file specified ({input_path}) does not exist.')
        if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)
        result = obj.deserialize.aaobject_to_folder(input=input_path, output_path=output_path)
        return result