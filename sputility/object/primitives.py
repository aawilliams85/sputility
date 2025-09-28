from datetime import datetime, timedelta, timezone
import struct
from warnings import warn

from . import enums
from . import types

PATTERN_OBJECT_VALUE = b'\xB1\x55\xD9\x51\x86\xB0\xD2\x11\xBF\xB1\x00\x10\x4B\x5F\x96\xA7'
PATTERN_END = b'\x00\x00\x00\x00\x00\x00\x00\x00'

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

def _seek_string_value_section(input: types.AaBinStream) -> str:
    # Buried inside the attribute section, there are string fields
    # where it is <length of object><length of string><string data>
    obj = _seek_binstream(input=input)
    value = _seek_string_var_len(input=obj)
    return value

def _seek_reference_section(input: types.AaBinStream) -> bytes:
    # No clue how to break this down further yet
    obj = _seek_binstream(input=input)
    return obj

def _seek_qualifiedenum_section(input: types.AaBinStream) -> types.AaQualifiedEnum:
    obj = _seek_binstream(input=input)
    text = _seek_string_var_len(input=obj)
    value = _seek_int(input=obj, length=2)
    unk01 = _seek_int(input=obj, length=2)
    unk02 = _seek_int(input=obj, length=2)
    return types.AaQualifiedEnum(
        text=text,
        value=value,
        unk01=unk01,
        unk02=unk02
    )

def _seek_international_string_value_section(input: types.AaBinStream) -> str:
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
    header = _seek_bytes(input=input, length=16)
    if header != PATTERN_OBJECT_VALUE: warn(f'Object value unexpected header: {header}')
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
        case enums.AaDataType.ReferenceType.value:
            value = _seek_reference_section(input=input)
        case enums.AaDataType.QualifiedEnumType.value:
            value = _seek_qualifiedenum_section(input=input)
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
        datatype=enums.AaDataType(datatype),
        value=value
    )

def _seek_end_section(input: types.AaBinStream):
    value = _seek_bytes(input=input, length=8)
    if value != PATTERN_END: warn(f'End Section unexpected value: {value}')
    return value