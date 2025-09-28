from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
import pprint
import struct

from .enums import *
from .types import *

def _filetime_to_datetime(input: bytes) -> datetime:
    filetime = struct.unpack('<Q', input[:8])[0]
    seconds = filetime // 10000000
    microseconds = (filetime % 10000000) // 10
    dt_utc = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds, microseconds=microseconds)
    return dt_utc

def _ticks_to_timedelta(input: int) -> timedelta:
    total_seconds = input / 10_000_000
    td = timedelta(seconds=total_seconds)
    return td

def _seek_pad(input: AaBinStream, length: int):
    input.offset += length

def _seek_bytes(input: AaBinStream, length: int = 4) -> AaBinStream:
    obj_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = obj_len
    value = input.data[input.offset:input.offset + length]
    input.offset += length
    return AaBinStream(
        data=value,
        offset=0
    )

def _seek_float(input: AaBinStream) -> float:
    length = 4
    value = struct.unpack('<f', input.data[input.offset:input.offset + length])[0]
    input.offset += length
    return value

def _seek_double(input: AaBinStream) -> float:
    length = 8
    value = struct.unpack('<d', input.data[input.offset:input.offset + length])[0]
    input.offset += length
    return value

def _seek_int(input: AaBinStream, length: int = 4) -> int:
    value = int.from_bytes(input.data[input.offset:input.offset + length], 'little')
    input.offset += length
    return value

def _seek_string(input: AaBinStream, length: int = 64) -> str:
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def _seek_string_var_len(input: AaBinStream, length: int = 4, mult: int = 1) -> str:
    # Some variable-length string fields start with 4 bytes to specify the length in bytes.
    # Other use 2 bytes to specify the length in characters.  For the latter specify length=2, mult=2.
    str_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = str_len * mult
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def _seek_string_value_section(input: AaBinStream, length: int = 4) -> str:
    # Buried inside the attribute section, there are string fields
    # where it is <length of object><length of string><string data>
    obj = _seek_bytes(input=input)
    value = _seek_string_var_len(input=obj)
    return value

def _seek_international_string_value_section(input: AaBinStream, length: int = 4) -> str:
    # Buried inside the attribute section, there are string fields
    # where it is <length of object><1><language id><length of string><string data>
    #
    # Would need to look at a multi-lang application to see how this changes
    obj = _seek_bytes(input=input)
    index = _seek_int(input=obj)
    locale_id = _seek_int(input=obj)
    value = _seek_string_var_len(input=obj)
    return value

def _seek_datetime_var_len(input: AaBinStream, length: int = 4) -> datetime:
    dt_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = dt_len
    value = _filetime_to_datetime(input.data[input.offset: input.offset + length])
    input.offset += length
    return value

def _seek_array(input: AaBinStream) -> list:
    _seek_pad(input=input, length=4)
    array_length = _seek_int(input=input, length=2)
    element_length = _seek_int(input=input, length=4)
    value = []
    for i in range(array_length):
        value.append(input.data[input.offset:input.offset + element_length])
        input.offset += element_length
    return value

def _seek_array_bool(input: AaBinStream) -> list[bool]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(bool(int.from_bytes(x, 'little')))
    return value

def _seek_array_int(input: AaBinStream) -> list[int]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(int.from_bytes(x, 'little'))
    return value

def _seek_array_float(input: AaBinStream) -> list[float]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(struct.unpack('<f', x)[0])
    return value

def _seek_array_double(input: AaBinStream) -> list[float]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(struct.unpack('<d', x)[0])
    return value

def _seek_array_string(input: AaBinStream) -> list[str]:
    _seek_pad(input=input, length=4)
    array_length = _seek_int(input=input, length=2)
    _seek_pad(input=input, length=4)
    value = []
    for i in range(array_length):
        obj = _seek_bytes(input=input)
        value_type = _seek_int(input=obj, length=1)
        obj2 = _seek_bytes(input=obj)
        string_value = _seek_string_var_len(input=obj2)
        value.append(string_value)
    return value

def _seek_array_datetime(input: AaBinStream) -> list[datetime]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(_filetime_to_datetime(x))
    return value

def _seek_array_timedelta(input: AaBinStream) -> list[datetime]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(_ticks_to_timedelta(int.from_bytes(x, 'little')))
    return value

def _get_header(input: AaBinStream) -> AaObjectHeader:
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

    # Trying to figure out whether this first
    # byte being inserted means it is a template.
    #
    # Instances seem to be one byte shorter in this section.
    may_be_is_template = not(bool(_seek_int(input=input, length=1)))
    if may_be_is_template:
        _seek_pad(input=input, length=1353)
    else:
        _seek_pad(input=input, length=1352)

    return AaObjectHeader(
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

def _get_attr(input: AaBinStream) -> AaObjectAttribute:
    _seek_pad(input=input, length=4)
    name = _seek_string_var_len(input=input, length=2, mult=2)
    attr_type = _seek_int(input=input, length=1)

    # It seems like these are probably four-bytes eache
    # but the enum ranges are small so maybe some bytes
    # are really reserved?
    array = bool(_seek_int(input=input))
    permission = _seek_int(input=input)
    write = _seek_int(input=input)
    locked = bool(_seek_int(input=input))

    parent_gobjectid = _seek_int(input=input, length=4)
    _seek_pad(input=input, length=8)
    parent_name = _seek_string_var_len(input=input, length=2, mult=2)
    _seek_pad(input=input, length=2)
    _seek_pad(input=input, length=16)
    value_type = _seek_int(input=input, length=1)
    value = None
    match value_type:
        case AaDataType.NoneType.value:
            raise NotImplementedError()
        case AaDataType.BooleanType.value:
            value = bool(_seek_int(input=input, length=1))
        case AaDataType.IntegerType.value:
            value = _seek_int(input=input, length=4)
        case AaDataType.FloatType.value:
            value = _seek_float(input=input)
        case AaDataType.DoubleType.value:
            value = _seek_double(input=input)
        case AaDataType.StringType.value:
            value = _seek_string_value_section(input=input)
        case AaDataType.TimeType.value:
            value = _seek_datetime_var_len(input=input)
        case AaDataType.ElapsedTimeType.value:
            value = _ticks_to_timedelta(_seek_int(input=input, length=8))
        case AaDataType.InternationalizedStringType.value:
            value = _seek_international_string_value_section(input=input)
        case AaDataType.BigStringType.value:
            raise NotImplementedError()
        case AaDataType.ArrayBooleanType.value:
            value = _seek_array_bool(input=input)
        case AaDataType.ArrayIntegerType.value:
            value = _seek_array_int(input=input)
        case AaDataType.ArrayFloatType.value:
            value = _seek_array_float(input=input)
        case AaDataType.ArrayDoubleType.value:
            value = _seek_array_double(input=input)
        case AaDataType.ArrayStringType.value:
            value = _seek_array_string(input=input)
        case AaDataType.ArrayTimeType.value:
            value = _seek_array_datetime(input=input)
        case AaDataType.ArrayElapsedTimeType.value:
            value = _seek_array_timedelta(input=input)
        case _:
            raise NotImplementedError()

    return AaObjectAttribute(
        name=name,
        attr_type=AaDataType(attr_type),
        array=array,
        permission=AaPermission(permission),
        write=AaWriteability(write),
        locked=locked,
        parent_gobjectid=parent_gobjectid,
        parent_name=parent_name,
        value_type=AaDataType(value_type),
        value=value
    )

def _get_content(input: AaBinStream) -> AaObjectContent:
    main_section_id = _seek_int(input=input, length=16)
    template_name = _seek_string(input=input)
    _seek_pad(input=input, length=596)
    attr_section_id = _seek_int(input=input, length=16)
    attr_count = _seek_int(input=input)
    attrs = []
    if attr_count > 0:
        for i in range(attr_count):
            attr = _get_attr(input=input)
            attrs.append(attr)

    # After the attribute section there seems to be an 8 byte null section
    _seek_pad(input=input, length=8)

    # Then there seem to be four NoneType objects
    for i in range(4): _seek_pad(input=input, length=17)

    # No clue
    _seek_pad(input=input, length=24)

    # Short desc object
    _seek_pad(input=input, length=17)
    short_desc = _seek_international_string_value_section(input=input)

    return AaObjectContent(
        main_section_id=main_section_id,
        template_name=template_name,
        attr_section_id=attr_section_id,
        attr_count=attr_count,
        attr_section=attrs,
        short_desc=short_desc
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
    
    aaobj = AaBinStream(
        data=aaobject_bytes,
        offset=0
    )
    header = _get_header(input=aaobj)
    pprint.pprint(header)
    print('')

    attrs = _get_content(input=aaobj)
    pprint.pprint(attrs)
    print('')