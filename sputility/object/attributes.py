from . import enums
from . import primitives
from . import types

def get_attr_type1(input: types.AaBinStream) -> types.AaObjectAttribute:
    primitives._seek_forward(input=input, length=2)
    id = primitives._seek_int(input=input, length=2)
    name = primitives._seek_string_var_len(input=input, length=2, mult=2)
    attr_type = primitives._seek_int(input=input, length=1)

    # It seems like these are probably four-bytes each
    # but the enum ranges are small so maybe some bytes
    # are really reserved?
    array = bool(primitives._seek_int(input=input))
    permission = primitives._seek_int(input=input)
    write = primitives._seek_int(input=input)
    locked = primitives._seek_int(input=input)

    parent_gobjectid = primitives._seek_int(input=input, length=4)
    primitives._seek_forward(input=input, length=8)
    parent_name = primitives._seek_string_var_len(input=input, length=2, mult=2)
    primitives._seek_forward(input=input, length=2)
    value = primitives._seek_object_value(input=input)

    return types.AaObjectAttribute(
        id=id,
        name=name,
        attr_type=enums.AaDataType(attr_type),
        array=array,
        permission=enums.AaPermission(permission),
        write=enums.AaWriteability(write),
        locked=enums.AaLocked(locked),
        parent_gobjectid=parent_gobjectid,
        parent_name=parent_name,
        source=None,
        value=value,
        primitive_name=None
    )

def get_attr_type2(input: types.AaBinStream) -> types.AaObjectAttribute:
    # Why is this backwards from the user defined attributes??
    # Thanks WW
    id = primitives._seek_int(input=input, length=2)
    primitives._seek_forward(input=input, length=2)
    attr_type = enums.AaDataType.Undefined

    # This needs more follow-up tests with multiple levels
    # of derivation.  It's not clear yet what some of these
    # bytes are doing and where things like the lock/write
    # values end up.
    if not(primitives._lookahead_pattern(input=input, pattern=primitives.PATTERN_OBJECT_VALUE)):
        primitives._seek_forward(input=input, length=4) # length of name FFFFFFFF or 00000000 ??
        attr_type = primitives._seek_int(input=input, length=1)
        primitives._seek_forward(input=input, length=11) # ???

    value = primitives._seek_object_value(input=input)
    return types.AaObjectAttribute(
        id=id,
        name=None,
        attr_type=enums.AaDataType(attr_type),
        array=None,
        permission=None,
        write=None,
        locked=None,
        parent_gobjectid=None,
        parent_name=None,
        source=None,
        value=value,
        primitive_name=None
    )