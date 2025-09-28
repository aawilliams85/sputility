from collections.abc import Callable
import os
from typing import Optional
from warnings import warn

from .object import deserialize
from .package import decompress

class SPUtility(object):
    def __init__(self):
        pass

    def decompress_package(
        self,
        input_path: str,
        output_path: str,
        progress: Optional[Callable[[str, int, int], None]] = None, 
    ):
        if not(os.path.isfile(input_path)): raise FileNotFoundError(f'Input file specified ({input_path}) does not exist.')
        if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)
        result = decompress.archive_to_disk(input_path=input_path, output_path=output_path)
        return result

    def explode_object(
        self,
        input_path: str,
        output_path: str,
        progress: Optional[Callable[[str, int, int], None]] = None, 
    ):
        if not(os.path.isfile(input_path)): raise FileNotFoundError(f'Input file specified ({input_path}) does not exist.')
        if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)
        result = deserialize.explode_aaobject(input=input_path, output_path=output_path)
        return result