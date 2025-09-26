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
class AaObjBin:
    data: bytes
    offset: int

@dataclass
class AaObjHeader:
    base_gobjectid: int
    is_template: bool       # <Obj>._IsTemplate
    this_gobjectid: int
    security_group: str     # <Obj>.SecurityGroup
    parent_gobjectid: int
    tagname: str            # <Obj>.Tagname
    contained_name: str     # <Obj>.ContainedName
    config_version: int     # <Obj>.ConfigVersion
    hierarchal_name: str    # <Obj>.HierarchalName
    host_name: str          # <Obj>.Host
    container_name: str     # <Obj>.Container
    area_name: str          # <Obj>.Area
    derived_from: str
    based_on: str           # <Obj>._BasedOn
    galaxy_name: str

@dataclass
class AaObjAttr:
    name: str
    datatype: AaObjAttrTypeEnum
    parent_gobjectid: int
    parent_name: str
    data: bool | int | float | str

@dataclass
class AaObjSection:
    main_section_id: int
    template_name: str
    attr_section_id: int
    attr_count: int
    attr_section: list[AaObjAttr]

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

def _seek_pad(input: AaObjBin, length: int):
    input.offset += length

def _seek_float(input: AaObjBin) -> float:
    length = 4
    value = struct.unpack('<f', input.data[input.offset:input.offset + length])
    input.offset += length
    return value

def _seek_double(input: AaObjBin) -> float:
    length = 8
    value = struct.unpack('<d', input.data[input.offset:input.offset + length])
    input.offset += length
    return value

def _seek_int(input: AaObjBin, length: int = 4) -> int:
    value = int.from_bytes(input.data[input.offset:input.offset + length], 'little')
    input.offset += length
    return value

def _seek_int_var_len(input: AaObjBin, length: int = 4) -> int:
    int_Len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = int_Len
    value = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    return value

def _seek_string(input: AaObjBin, length: int = 64) -> str:
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def _seek_string_var_len(input: AaObjBin, length: int = 4, mult: int = 1) -> str:
    # Some variable-length string fields start with 4 bytes to specify the length in bytes.
    # Other use 2 bytes to specify the length in characters.  For the latter specify length=2, mult=2.
    str_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = str_len * mult
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def _get_header(input: AaObjBin) -> AaObjHeader:
    base_gobjectid = _seek_int(input=input)

    # If this is a template there will be four null bytes
    # Otherwise if those bytes are missing, it is an instance
    check_is_template = _seek_int(input=input)
    if check_is_template:
        is_template = False
        input.offset -= 4
    else:
        is_template = True

    _seek_pad(input=input, length=4)
    this_gobjectid = _seek_int(input=input)
    _seek_pad(input=input, length=12)
    security_group = _seek_string(input=input)
    _seek_pad(input=input, length=12)
    parent_gobject_id = _seek_int(input=input)
    _seek_pad(input=input, length=52)
    tagname = _seek_string(input=input)
    _seek_pad(input=input, length=596)
    contained_name = _seek_string(input=input)
    _seek_pad(input=input, length=4)
    _seek_pad(input=input, length=32)
    config_version = _seek_int(input=input)
    _seek_pad(input=input, length=16)
    hierarchal_name = _seek_string(input=input, length=130)
    _seek_pad(input=input, length=530)
    host_name = _seek_string(input=input)
    _seek_pad(input=input, length=2)
    container_name = _seek_string(input=input)
    _seek_pad(input=input, length=596)
    area_name = _seek_string(input=input)
    _seek_pad(input=input, length=2)
    derived_from = _seek_string(input=input)
    _seek_pad(input=input, length=596)
    based_on = _seek_string(input=input)
    _seek_pad(input=input, length=528)
    galaxy_name = _seek_string_var_len(input=input)
    print(f'Offset: {input.offset}')
    _seek_pad(input=input, length=1354)

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

def _get_attr(input: AaObjBin) -> AaObjAttr:
    _seek_pad(input=input, length=4)
    name = _seek_string_var_len(input=input, length=2, mult=2)
    datatype = _seek_int(input=input, length=1)
    _seek_pad(input=input, length=16)
    parent_gobjectid = _seek_int(input=input, length=4)
    _seek_pad(input=input, length=8)
    parent_name = _seek_string_var_len(input=input, length=2, mult=2)
    _seek_pad(input=input, length=2)
    _seek_pad(input=input, length=17)
    data = None
    match datatype:
        case AaObjAttrTypeEnum.NoneType.value:
            raise NotImplementedError()
        case AaObjAttrTypeEnum.BooleanType.value:
            data = bool(_seek_int(input=input, length=1))
        case AaObjAttrTypeEnum.IntegerType.value:
            data = _seek_int(input=input, length=4)
        case AaObjAttrTypeEnum.FloatType.value:
            data = _seek_float(input=input)
        case AaObjAttrTypeEnum.DoubleType.value:
            data = _seek_double(input=input)
        case AaObjAttrTypeEnum.StringType.value:
            data = _seek_string_var_len(input=input)
        case AaObjAttrTypeEnum.TimeType.value:
            data = _seek_int_var_len(input=input)
        case AaObjAttrTypeEnum.ElapsedTimeType.value:
            data = _seek_int(input=input, length=8)
        case AaObjAttrTypeEnum.InternationalizedStringType.value:
            data = _seek_string_var_len(input=input)
        case AaObjAttrTypeEnum.BigStringType.value:
            raise NotImplementedError()
        case _:
            raise NotImplementedError()

    return AaObjAttr(
        name=name,
        datatype=AaObjAttrTypeEnum(datatype),
        parent_gobjectid=parent_gobjectid,
        parent_name=parent_name,
        data=data
    )

def _get_attrs(input: AaObjBin) -> AaObjSection:
    main_section_id = _seek_int(input=input, length=16)
    template_name = _seek_string(input=input)
    _seek_pad(input=input, length=596)
    attr_section_id = _seek_int(input=input, length=16)
    print(f'Count Offset: {input.offset}')
    attr_count = _seek_int(input=input)
    print(attr_count)
    attrs = []
    if attr_count > 0:
        for i in range(attr_count):
            attr = _get_attr(input=input)
            attrs.append(attr)

    return AaObjSection(
        main_section_id=main_section_id,
        template_name=template_name,
        attr_section_id=attr_section_id,
        attr_count=attr_count,
        attr_section=attrs
    )

def explode_aaobject(
    input: str | bytes,
    output_path: str
):
    # Create output folder if it doesn't exist yet
    if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)

    aaobject_bytes: bytes

    if isinstance(input, (str, os.PathLike)):
        print(input)
        try:
            with open(input, 'rb') as file:
                aaobject_bytes = file.read()
        except:
            pass
    elif isinstance(input, bytes):
        aaobject_bytes = bytes(input)
    else:
        raise TypeError('Input must be a file path (str/PathLike) or bytes.')
    
    aaobj = AaObjBin(
        data=aaobject_bytes,
        offset=0
    )
    header = _get_header(input=aaobj)
    pprint.pprint(header)
    print('')

    attrs = _get_attrs(input=aaobj)
    pprint.pprint(attrs)
    print('')