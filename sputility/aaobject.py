from dataclasses import dataclass, field
from enum import IntEnum
import os
import pprint
import struct

class AaObjAttrTypeEnum(IntEnum):
    NoneType = 0
    BooleanType = 1
    IntegerType = 2
    FloatType = 3
    DoubleType = 4
    StringType = 5
    TimeType = 6
    ElapsedTimeType = 7
    ReferenceType = 8
    StatusType = 9
    DataTypeType = 10
    SecurityClassificationType = 11
    DataQualityType = 12
    QualifiedEnumType = 13
    QualifiedStructType = 14
    InternationalizedStringType = 15
    BigStringType = 16

@dataclass
class AaObj:
    data: bytes
    offset: int

@dataclass
class AaObjHeader:
    base_gobjectid: int
    is_template: bool
    this_gobjectid: int
    security_group: str
    parent_gobjectid: int
    tagname: str
    contained_name: str
    config_version: int
    hierarchal_name: str
    host_name: str
    container_name: str
    area_name: str
    derived_from: str
    based_on: str
    galaxy_name: str

@dataclass
class AaObjAttrHeader:
    unk01: int
    unk02: int
    name_len: int
    name: str
    datatype: AaObjAttrTypeEnum
    unk03: int
    unk04: int
    unk05: int
    unk06: int
    parent_gobjectid: int
    unk07: int
    unk08: int
    parent_name_len: int
    parent_name: str
    unk09: int
    magic: bytes
    data: bytes

def _seek_pad(input: AaObj, length: int):
    input.offset += length

def _seek_fixed_int(input: AaObj, length: int = 4) -> int:
    value = int.from_bytes(input.data[input.offset:input.offset + length], 'little')
    input.offset += length
    return value

def _seek_fixed_string(input: AaObj, length: int = 64) -> str:
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def _seek_variable_string(input: AaObj) -> str:
    length = 4
    str_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = str_len
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def get_header(input: AaObj) -> AaObjHeader:
    # Base Object ID (ex: UserDefined or other built-in object)
    base_gobjectid = _seek_fixed_int(input=input)

    # If this is a template there will be four null bytes
    # Otherwise if those bytes are missing, it is an instance
    check_is_template = _seek_fixed_int(input=input)
    if check_is_template:
        is_template = False
        input.offset -= 4
    else:
        is_template = True

    _seek_pad(input=input, length=4)
    this_gobjectid = _seek_fixed_int(input=input)
    _seek_pad(input=input, length=12)
    security_group = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=12)
    parent_gobject_id = _seek_fixed_int(input=input)
    _seek_pad(input=input, length=52)
    tagname = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=596)
    contained_name = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=4)
    _seek_pad(input=input, length=32)
    config_version = _seek_fixed_int(input=input)
    _seek_pad(input=input, length=16)
    hierarchal_name = _seek_fixed_string(input=input, length=130)
    _seek_pad(input=input, length=530)
    host_name = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=2)
    container_name = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=596)
    area_name = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=2)
    derived_from = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=596)
    based_on = _seek_fixed_string(input=input)
    _seek_pad(input=input, length=528)
    galaxy_name = _seek_variable_string(input=input)

    return AaObjHeader(
        base_gobjectid=base_gobjectid,
        is_template=is_template,
        this_gobjectid=this_gobjectid,
        security_group=security_group,
        parent_gobjectid=parent_gobject_id,
        tagname=tagname,
        contained_name=contained_name,
        config_version=config_version,
        hierarchal_name=hierarchal_name,
        host_name=host_name,
        container_name=container_name,
        area_name=area_name,
        derived_from=derived_from,
        based_on=based_on,
        galaxy_name=galaxy_name
    )

def explode_aaobject(
    input: str | bytes,
    output_path: str
):
    # Create output folder if it doesn't exist yet
    if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)

    aaobject_bytes: bytes

    if isinstance(input, (str, os.PathLike)):
        try:
            with open(input, 'rb') as file:
                aaobject_bytes = file.read()
        except:
            pass
    elif isinstance(input, bytes):
        aaobject_bytes = bytes(input)
    else:
        raise TypeError('Input must be a file path (str/PathLike) or bytes.')
    
    aaobj = AaObj(
        data=aaobject_bytes,
        offset=0
    )
    header = get_header(input=aaobj)
    pprint.pprint(header)
    print('')