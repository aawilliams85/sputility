from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
import struct
from warnings import warn

from . import enums
from . import types

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

def _seek_pad(input: types.AaBinStream, length: int):
    input.offset += length

def _seek_bytes(input: types.AaBinStream, length: int = 4) -> bytes:
    value = input.data[input.offset:input.offset + length]
    input.offset += length
    return value

def _seek_binstream(input: types.AaBinStream, length: int = 4) -> types.AaBinStream:
    obj_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = obj_len
    value = input.data[input.offset:input.offset + length]
    input.offset += length
    return types.AaBinStream(
        data=value,
        offset=0
    )

def _seek_float(input: types.AaBinStream) -> float:
    length = 4
    value = struct.unpack('<f', input.data[input.offset:input.offset + length])[0]
    input.offset += length
    return value

def _seek_double(input: types.AaBinStream) -> float:
    length = 8
    value = struct.unpack('<d', input.data[input.offset:input.offset + length])[0]
    input.offset += length
    return value

def _seek_int(input: types.AaBinStream, length: int = 4) -> int:
    value = int.from_bytes(input.data[input.offset:input.offset + length], 'little')
    input.offset += length
    return value

def _seek_string(input: types.AaBinStream, length: int = 64) -> str:
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def _seek_string_var_len(input: types.AaBinStream, length: int = 4, mult: int = 1) -> str:
    # Some variable-length string fields start with 4 bytes to specify the length in bytes.
    # Other use 2 bytes to specify the length in characters.  For the latter specify length=2, mult=2.
    str_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = str_len * mult
    value = input.data[input.offset: input.offset + length].decode(encoding='utf-16-le').rstrip('\x00')
    input.offset += length
    return value

def _seek_string_value_section(input: types.AaBinStream, length: int = 4) -> str:
    # Buried inside the attribute section, there are string fields
    # where it is <length of object><length of string><string data>
    obj = _seek_binstream(input=input)
    value = _seek_string_var_len(input=obj)
    return value

def _seek_international_string_value_section(input: types.AaBinStream, length: int = 4) -> str:
    # Buried inside the attribute section, there are string fields
    # where it is <length of object><1><language id><length of string><string data>
    #
    # Would need to look at a multi-lang application to see how this changes
    obj = _seek_binstream(input=input)
    index = _seek_int(input=obj)
    locale_id = _seek_int(input=obj)
    value = _seek_string_var_len(input=obj)
    return value

def _seek_datetime_var_len(input: types.AaBinStream, length: int = 4) -> datetime:
    dt_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = dt_len
    value = _filetime_to_datetime(input.data[input.offset: input.offset + length])
    input.offset += length
    return value

def _seek_array(input: types.AaBinStream) -> list:
    _seek_pad(input=input, length=4)
    array_length = _seek_int(input=input, length=2)
    element_length = _seek_int(input=input, length=4)
    value = []
    for i in range(array_length):
        value.append(input.data[input.offset:input.offset + element_length])
        input.offset += element_length
    return value

def _seek_array_bool(input: types.AaBinStream) -> list[bool]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(bool(int.from_bytes(x, 'little')))
    return value

def _seek_array_int(input: types.AaBinStream) -> list[int]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(int.from_bytes(x, 'little'))
    return value

def _seek_array_float(input: types.AaBinStream) -> list[float]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(struct.unpack('<f', x)[0])
    return value

def _seek_array_double(input: types.AaBinStream) -> list[float]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(struct.unpack('<d', x)[0])
    return value

def _seek_array_string(input: types.AaBinStream) -> list[str]:
    _seek_pad(input=input, length=4)
    array_length = _seek_int(input=input, length=2)
    _seek_pad(input=input, length=4)
    value = []
    for i in range(array_length):
        obj = _seek_binstream(input=input)
        value_type = _seek_int(input=obj, length=1)
        obj2 = _seek_binstream(input=obj)
        string_value = _seek_string_var_len(input=obj2)
        value.append(string_value)
    return value

def _seek_array_datetime(input: types.AaBinStream) -> list[datetime]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(_filetime_to_datetime(x))
    return value

def _seek_array_timedelta(input: types.AaBinStream) -> list[datetime]:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(_ticks_to_timedelta(int.from_bytes(x, 'little')))
    return value

def _seek_object_value(input: types.AaBinStream) -> types.AaObjectValue:
    expected_header = b'\xB1\x55\xD9\x51\x86\xB0\xD2\x11\xBF\xB1\x00\x10\x4B\x5F\x96\xA7'
    header = _seek_bytes(input=input, length=16)
    if header != expected_header: warn(f'Prim1 unexpected header: {header}')
    datatype = _seek_int(input=input, length=1)
    value = None
    match datatype:
        case enums.AaDataType.NoneType.value:
            value = None
        case enums.AaDataType.BooleanType.value:
            value = bool(_seek_int(input=input, length=1))
        case enums.AaDataType.IntegerType.value:
            value = _seek_int(input=input, length=4)
        case enums.AaDataType.FloatType.value:
            value = _seek_float(input=input)
        case enums.AaDataType.DoubleType.value:
            value = _seek_double(input=input)
        case enums.AaDataType.StringType.value:
            value = _seek_string_value_section(input=input)
        case enums.AaDataType.TimeType.value:
            value = _seek_datetime_var_len(input=input)
        case enums.AaDataType.ElapsedTimeType.value:
            value = _ticks_to_timedelta(_seek_int(input=input, length=8))
        case enums.AaDataType.InternationalizedStringType.value:
            value = _seek_international_string_value_section(input=input)
        case enums.AaDataType.BigStringType.value:
            raise NotImplementedError()
        case enums.AaDataType.ArrayBooleanType.value:
            value = _seek_array_bool(input=input)
        case enums.AaDataType.ArrayIntegerType.value:
            value = _seek_array_int(input=input)
        case enums.AaDataType.ArrayFloatType.value:
            value = _seek_array_float(input=input)
        case enums.AaDataType.ArrayDoubleType.value:
            value = _seek_array_double(input=input)
        case enums.AaDataType.ArrayStringType.value:
            value = _seek_array_string(input=input)
        case enums.AaDataType.ArrayTimeType.value:
            value = _seek_array_datetime(input=input)
        case enums.AaDataType.ArrayElapsedTimeType.value:
            value = _seek_array_timedelta(input=input)
        case _:
            raise NotImplementedError()
    return types.AaObjectValue(
        header=header,
        datatype=datatype,
        value=value
    )

def _get_header(input: types.AaBinStream) -> types.AaObjectHeader:
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

    return types.AaObjectHeader(
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

def _get_attr(input: types.AaBinStream) -> types.AaObjectAttribute:
    _seek_pad(input=input, length=4)
    name = _seek_string_var_len(input=input, length=2, mult=2)
    attr_type = _seek_int(input=input, length=1)

    # It seems like these are probably four-bytes eache
    # but the enum ranges are small so maybe some bytes
    # are really reserved?
    array = bool(_seek_int(input=input))
    permission = _seek_int(input=input)
    write = _seek_int(input=input)
    locked = _seek_int(input=input)

    parent_gobjectid = _seek_int(input=input, length=4)
    _seek_pad(input=input, length=8)
    parent_name = _seek_string_var_len(input=input, length=2, mult=2)
    _seek_pad(input=input, length=2)
    value_prim = _seek_object_value(input=input)

    return types.AaObjectAttribute(
        name=name,
        attr_type=enums.AaDataType(attr_type),
        array=array,
        permission=enums.AaPermission(permission),
        write=enums.AaWriteability(write),
        locked=enums.AaLocked(locked),
        parent_gobjectid=parent_gobjectid,
        parent_name=parent_name,
        value_type=enums.AaDataType(value_prim.datatype),
        value=value_prim.value
    )

def _get_content(input: types.AaBinStream) -> types.AaObjectContent:
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
    for i in range(4): _seek_object_value(input=input)

    # No clue
    _seek_pad(input=input, length=24)

    # Short desc object
    short_desc = _seek_object_value(input=input).value

    return types.AaObjectContent(
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
    
    aaobj = types.AaBinStream(
        data=aaobject_bytes,
        offset=0
    )
    header = _get_header(input=aaobj)
    content = _get_content(input=aaobj)
    return types.AaObject(
        header=header,
        content=content
    )