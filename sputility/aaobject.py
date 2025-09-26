from dataclasses import dataclass, field
from enum import IntEnum
import os
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
    base_gobjectid = int.from_bytes(input[offset:offset + 4], 'little')
    offset += 4

    # If this is a template there will be four null bytes
    # Otherwise if those bytes are missing, it is an instance
    check_is_template = int.from_bytes(input[offset:offset + 4], 'little')
    if check_is_template:
        is_template = False
    else:
        is_template = True
        offset += 4

    # Unknown
    unk01 = int.from_bytes(input[offset: offset + 4], 'little')
    offset += 4

    # Object ID
    this_gobjectid = int.from_bytes(input[offset:offset + 4], 'little')
    offset += 4

    # Unknown
    unk02 = int.from_bytes(input[offset: offset + 4], 'little')
    offset += 4

    # Unknown
    unk03 = int.from_bytes(input[offset: offset + 8], 'little')
    offset += 8

    # Security Group name
    security_group = input[offset: offset + 64].decode(encoding='utf-16-le').rstrip('\x00')
    offset += 64

    # Unknown
    unk04 = int.from_bytes(input[offset: offset + 4], 'little')
    offset += 4

    # Unknown
    unk05 = int.from_bytes(input[offset: offset + 4], 'little')
    offset += 4

    # Unknown
    unk06 = int.from_bytes(input[offset: offset + 4], 'little')
    offset += 4

    # Parent Template ID
    parent_gobject_id = int.from_bytes(input[offset: offset + 4], 'little')
    offset += 4

    return AaObjHeader(
        base_gobjectid=base_gobjectid,
        is_template=is_template,
        this_gobjectid=this_gobjectid,
        security_group=security_group,
        parent_gobjectid=parent_gobject_id
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
    print(header)