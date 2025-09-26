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
    area_name: str
    container_name: str

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

def get_header(input: bytes) -> AaObjHeader:
    offset = 0

    # Base Object ID (ex: UserDefined or other built-in object)
    length = 4
    base_gobjectid = int.from_bytes(input[offset:offset + length], 'little')
    offset += length

    # If this is a template there will be four null bytes
    # Otherwise if those bytes are missing, it is an instance
    length = 4
    check_is_template = int.from_bytes(input[offset:offset + length], 'little')
    if check_is_template:
        is_template = False
    else:
        is_template = True
        offset += length

    # Unknown
    offset += 4

    # Object ID
    length = 4
    this_gobjectid = int.from_bytes(input[offset:offset + length], 'little')
    offset += length

    # Unknown
    offset += 12

    # Security Group name
    length = 64
    security_group = input[offset: offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    offset += length

    # Unknown
    offset += 12

    # Parent Template ID
    length = 4
    parent_gobject_id = int.from_bytes(input[offset: offset + length], 'little')
    offset += length

    # Unknown
    offset += 52

    # Security Group name
    length = 64
    tagname = input[offset: offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    offset += length

    # Unknown
    offset += 596

    # Contained Name
    length = 64
    contained_name = input[offset: offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    offset += length

    # Unknown
    offset += 4

    # Unknown
    offset += 32

    # Config Version
    length = 4
    config_version = int.from_bytes(input[offset: offset + length], 'little')
    offset += length

    # Unknown
    offset += 16

    # Hierarchal Name
    length = 130
    hierarchal_name = input[offset: offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    offset += length

    # Unknown
    offset += 530

    # Area Name
    length = 64
    area_name = input[offset: offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    offset += length

    # Unknown
    offset += 2

    # Container Name
    length = 64
    container_name = input[offset: offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    offset += length

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
        area_name=area_name,
        container_name=container_name
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
    
    header = get_header(aaobject_bytes)
    pprint.pprint(header)
    print('')