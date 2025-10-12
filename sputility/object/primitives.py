from datetime import datetime, timedelta, timezone
import struct
from warnings import warn

from . import enums
from . import types

PATTERN_OBJECT_VALUE = b'\xB1\x55\xD9\x51\x86\xB0\xD2\x11\xBF\xB1\x00\x10\x4B\x5F\x96\xA7'
PATTERN_TEMPLATE_VALUE = b'\x00\x00\x00\x00'
PATTERN_END = b'\x00\x00\x00\x00\x00\x00\x00\x00'
PATTERN_END_OF_FILE = b'\x00\x00\x00\x00'
PATTERN_END_OF_HEADER = b'\x00\x00\x00\x00'

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

def _lookahead_bytes(input: types.AaBinStream, length: int) -> bytes:
    if ((input.offset + length) > len(input.data)): raise MemoryError(f'Memory bounds exceeded.  Size: {len(input.data):0X}, Offset: {input.offset:0X}, Length: {length:0X}.')
    value = input.data[input.offset:input.offset + length]
    return value

def _lookahead_bool(input: types.AaBinStream) -> bool:
    value = bool(int.from_bytes(_lookahead_bytes(input=input, length=1), 'little'))
    return value

def _lookahead_int(input: types.AaBinStream, length: int = 4) -> int:
    value = int.from_bytes(_lookahead_bytes(input=input, length=length), 'little')
    return value

def _lookahead_pattern(input: types.AaBinStream, pattern: bytes) -> bool:
    actual = input.data[input.offset:input.offset + len(pattern)]
    return (actual == pattern)

def _lookahead_multipattern(input: types.AaBinStream, patterns: list[bytes]) -> bool:
    for x in patterns:
        if _lookahead_pattern(input=input, pattern=x): return True
    return False

def _lookahead_string_var_len(input: types.AaBinStream, length: int = 4, mult: int = 1, decode: str = 'utf-16le') -> bool:
    # Some variable-length string fields start with 4 bytes to specify the length in bytes.
    # Other use 2 bytes to specify the length in characters.  For the latter specify length=2, mult=2.
    str_len = _lookahead_int(input=input, length=length)
    data_len = str_len * mult
    total_len = length + data_len
    #print(f'Data Length: {data_len}, Total Length: {total_len}')
    data = _lookahead_bytes(input=input, length=total_len)
    obj = types.AaBinStream(
        data=data,
        offset=0
    )
    value = _seek_string_var_len(input=obj).rstrip('\x00')
    expected_len = (str_len - 2) / (2 * mult)
    #print(f'Value: {value}, Expected Length: {expected_len}, Actual Length: {len(value)}')
    if (len(value) < 1): return False
    if (len(value) != expected_len): return False
    return value

def _seek_forward(input: types.AaBinStream, length: int):
    # Anywhere this is called, basically means that I don't
    # understand what a range of bytes means and want to skip
    # past it.
    _seek_bytes(input=input, length=length)

def _seek_bytes(input: types.AaBinStream, length: int = 4) -> bytes:
    if ((input.offset + length) > len(input.data)): raise MemoryError(f'Memory bounds exceeded.  Size: {len(input.data):0X}, Offset: {input.offset:0X}, Length: {length:0X}.')
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

def _seek_bool(input: types.AaBinStream) -> bool:
    value = bool(_seek_int(input=input, length=1))
    return value

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

def _seek_string(input: types.AaBinStream, length: int = 64, decode: str = 'utf-16le') -> str:
    data = _seek_bytes(input=input, length=length)
    value = data.decode(decode).rstrip('\x00')
    return value

def _seek_string_var_len(input: types.AaBinStream, length: int = 4, mult: int = 1, decode: str = 'utf-16le') -> str:
    # Some variable-length string fields start with 4 bytes to specify the length in bytes.
    # Other use 2 bytes to specify the length in characters.  For the latter specify length=2, mult=2.
    str_len = int.from_bytes(input.data[input.offset: input.offset + length], 'little')
    input.offset += length
    length = str_len * mult
    data = _seek_bytes(input=input, length=length)
    value = data.decode(decode).rstrip('\x00')
    return value

def _seek_string_value_section(input: types.AaBinStream) -> str:
    # Buried inside the attribute section, there are string fields
    # where it is <length of object><length of string><string data>
    obj = _seek_binstream(input=input)
    value = _seek_string_var_len(input=obj)
    return value

def _seek_reference_section(input: types.AaBinStream) -> types.AaReference:
    obj = _seek_binstream(input=input)

    # This length is notably strange because the upper two bytes
    # seem to be unrelated.  So it is 2 bytes for length, 2 bytes
    # unknown, then data.  Need to test if this is a general rule
    # throughout or just these sections.
    refa_len = _seek_int(input=obj, length=2)
    unk01 = _seek_int(input=obj, length=2)
    refa_text = _seek_string(input=obj, length=refa_len)

    refb_text = _seek_string_var_len(input=obj)
    _seek_forward(input=obj, length=20)
    warn(f'ReferenceType not fully decoded yet, offset: {input.offset:0X}.')
    return types.AaReference(
        refA=refa_text,
        refB=refb_text
    )

def _seek_status_section(input: types.AaBinStream) -> int:
    warn(f'StatusType not decoded yet, offset: {input.offset:0X}.')
    obj = _seek_binstream(input=input)
    value = _seek_bytes(input=obj, length=len(obj.data))
    return value

def _seek_datatype_section(input: types.AaBinStream) -> int:
    warn(f'DataTypeType not decoded yet, offset: {input.offset:0X}.')
    value = _seek_bytes(input=input)
    return value

def _seek_qualifiedenum_section(input: types.AaBinStream) -> types.AaQualifiedEnum:
    obj = _seek_binstream(input=input)
    value = _seek_string_var_len(input=obj)
    ordinal = _seek_int(input=obj, length=2)
    primitive_id = _seek_int(input=obj, length=2)
    attribute_id = _seek_int(input=obj, length=2)
    return types.AaQualifiedEnum(
        value=value,
        ordinal=ordinal,
        primitive_id=primitive_id,
        attribute_id=attribute_id
    )

def _seek_qualifiedstruct_section(input: types.AaBinStream) -> types.AaQualifiedStruct:
    warn(f'QualifiedStruct not decoded yet, offset: {input.offset:0X}.')
    obj = _seek_binstream(input=input)
    unk01 = _seek_int(input=obj)
    unk02 = _seek_int(input=obj)
    unk03 = _seek_int(input=obj, length=2)
    unk04 = _seek_int(input=obj, length=2)
    unk05 = _seek_int(input=obj)
    return types.AaQualifiedStruct(
        unk01=unk01,
        unk02=unk02,
        unk03=unk03,
        unk04=unk04,
        unk05=unk05
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
    _seek_forward(input=input, length=4)
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
    _seek_forward(input=input, length=4)
    array_length = _seek_int(input=input, length=2)
    _seek_forward(input=input, length=4)
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

def _seek_array_reference(input: types.AaBinStream) -> list[types.AaReference]:
    warn(f'ArrayReference not decoded yet, offset: {input.offset:0X}.')
    _seek_forward(input=input, length=4)
    array_length = _seek_int(input=input, length=2)
    _seek_forward(input=input, length=4)
    value = []
    for i in range(array_length):
        obj = _seek_binstream(input=input)

        # This length is notably strange because the upper two bytes
        # seem to be unrelated.  So it is 2 bytes for length, 2 bytes
        # unknown, then data.  Need to test if this is a general rule
        # throughout or just these sections.
        unk00 = _seek_bytes(input=obj, length=5)
        refa_len = _seek_int(input=obj, length=2)
        refa_unk01 = _seek_int(input=obj, length=2)
        refa_text = _seek_string(input=obj, length=refa_len)
        refa_unk02 = _seek_int(input=obj, length=4)
        refa_text2 = _seek_string(input=obj, length=refa_unk02)
        refa_unk03 = _seek_int(input=obj, length=4)

        refb_len = _seek_int(input=obj, length=2)
        unk04 = _seek_int(input=obj, length=2)
        refb_text = _seek_string(input=obj, length=refb_len)
        _seek_forward(input=obj, length=8)
        _seek_forward(input=obj, length=12)
        value.append(types.AaReference(
            refA=refa_text,
            refB=refb_text
        ))

    return value

def _seek_array_datatype(input: types.AaBinStream) -> list:
    obj = _seek_array(input=input)
    value = []
    for x in obj: value.append(x)
    return value

def _seek_object_value(input: types.AaBinStream, raise_mismatch: bool = True) -> types.AaObjectValue:
    # The meaning of these header bytes is unclear except that
    # they seem to sit ahead of all the Value objects.  If a mistake
    # has been made walking through the binary somewhere else,
    # this can catch the deserialization at the next attribute after
    # the mistake.
    header = _seek_bytes(input=input, length=16)
    if header != PATTERN_OBJECT_VALUE:
        warn(f'Object value unexpected header: {header}')
        if raise_mismatch: raise Exception(f'Pattern mismatch at {input.offset:0X}')

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
        case enums.AaDataType.StatusType.value:
            value = _seek_status_section(input=input)
        case enums.AaDataType.DataTypeType.value:
            value = _seek_datatype_section(input=input)
        case enums.AaDataType.QualifiedEnumType.value:
            value = _seek_qualifiedenum_section(input=input)
        case enums.AaDataType.QualifiedStructType.value:
            value = _seek_qualifiedstruct_section(input=input)
        case enums.AaDataType.InternationalizedStringType.value:
            value = _seek_international_string_value_section(input=input)
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
        case enums.AaDataType.ArrayReferenceType.value:
            value = _seek_array_reference(input=input)
        case enums.AaDataType.ArrayDataTypeType.value:
            value = _seek_array_datatype(input=input)
        case _:
            raise NotImplementedError(f'Data type {datatype} not implemented at offset {input.offset:0X}.')
    return types.AaObjectValue(
        datatype=enums.AaDataType(datatype),
        value=value
    )

def _seek_end_section(input: types.AaBinStream, raise_mismatch: bool = True):
    # The meaning of these header bytes is unclear except that
    # they seem to sit behind certain objects.  If a mistake
    # has been made walking through the binary somewhere else,
    # this can catch the deserialization at the next object after
    # the mistake.
    value = _seek_bytes(input=input, length=8)
    if value != PATTERN_END:
        warn(f'End Section unexpected value: {value}')
        if raise_mismatch: raise Exception(f'Pattern mismatch at {input.offset:0X}')
    return value