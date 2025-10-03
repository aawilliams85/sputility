import os
import struct

from . import enums
from . import primitives
from . import types

PATTERN_OBJECT_VALUE = b'\xB1\x55\xD9\x51\x86\xB0\xD2\x11\xBF\xB1\x00\x10\x4B\x5F\x96\xA7'
PATTERN_END = b'\x00\x00\x00\x00\x00\x00\x00\x00'

def _get_header(input: types.AaBinStream) -> types.AaObjectHeader:
    base_gobjectid = primitives._seek_int(input=input)

    # If this is a template there will be four null bytes
    # Otherwise if those bytes are missing, it is an instance
    is_template = False
    if primitives._lookahead_pattern(input=input, pattern=primitives.PATTERN_TEMPLATE_VALUE):
        is_template =  True
        primitives._seek_forward(input=input, length=4)

    primitives._seek_forward(input=input, length=4)
    this_gobjectid = primitives._seek_int(input=input)
    primitives._seek_forward(input=input, length=12)
    security_group = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=12)
    parent_gobject_id = primitives._seek_int(input=input)
    primitives._seek_forward(input=input, length=52)
    tagname = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=596)
    contained_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=4)
    primitives._seek_forward(input=input, length=32)
    config_version = primitives._seek_int(input=input)
    primitives._seek_forward(input=input, length=16)
    hierarchal_name = primitives._seek_string(input=input, length=130)
    primitives._seek_forward(input=input, length=530)
    host_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=2)
    container_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=596)
    area_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=2)
    derived_from = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=596)
    based_on = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=528)
    galaxy_name = primitives._seek_string_var_len(input=input)

    # Trying to figure out whether this first
    # byte being inserted means it is a template.
    #
    # Instances seem to be one byte shorter in this section.
    may_be_is_template = not(bool(primitives._seek_int(input=input, length=1)))
    if may_be_is_template:
        primitives._seek_forward(input=input, length=1353)
    else:
        primitives._seek_forward(input=input, length=1352)

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

def _get_attr_type1(input: types.AaBinStream) -> types.AaObjectAttribute:
    primitives._seek_forward(input=input, length=2)
    id = primitives._seek_int(input=input, length=2)
    name = primitives._seek_string_var_len(input=input, length=2, mult=2)
    attr_type = primitives._seek_int(input=input, length=1)

    # It seems like these are probably four-bytes eache
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
        source=enums.AaSource.UserDefined,
        value=value
    )

def _get_attr_type2(input: types.AaBinStream) -> types.AaObjectAttribute:
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
        source=enums.AaSource.BuiltIn,
        value=value
    )

def _get_content(input: types.AaBinStream) -> types.AaObjectContent:
    main_section_id = primitives._seek_int(input=input, length=16)
    template_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=596)
    sections = []

    # User Defined Attributes ???
    header = primitives._seek_bytes(input=input, length=16)
    count = primitives._seek_int(input=input)
    attrs = []
    if count > 0:
        for i in range(count):
            attrs.append(_get_attr_type1(input=input))
    primitives._seek_end_section(input=input)
    sections.append(types.AaObjectAttributeSection(
        header=header,
        count=count,
        attributes=attrs
    ))

    # Then there seem to be four NoneType objects
    for i in range(4): primitives._seek_object_value(input=input)

    # Built-in attributes ???
    header = None
    count = primitives._seek_int(input=input)
    attrs = []
    if count > 0:
        for i in range(count):
            attrs.append(_get_attr_type2(input=input))
    sections.append(types.AaObjectAttributeSection(
        header=header,
        count=count,
        attributes=attrs
    ))

    # No clue
    unk = primitives._seek_int(input=input) # ???
    primitives._seek_forward(input=input, length=660)
    primitives._seek_forward(input=input, length=20) # Attribute ???
    primitives._seek_forward(input=input, length=664)
    unk_header = primitives._seek_bytes(input=input, length=16)
    unk_template_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=596)

    # Hidden attributed ???
    header = primitives._seek_bytes(input=input, length=16)
    count = primitives._seek_int(input=input)
    attrs = []
    if count > 0:
        for i in range(count):
            attrs.append(_get_attr_type1(input=input))
    primitives._seek_end_section(input=input)
    sections.append(types.AaObjectAttributeSection(
        header=header,
        count=count,
        attributes=attrs
    ))

    # Then there seem to be four NoneType objects
    for i in range(4): primitives._seek_object_value(input=input)

    header = None
    count = primitives._seek_int(input=input)
    attrs = []
    if count > 0:
        for i in range(count):
            attrs.append(_get_attr_type2(input=input))
    sections.append(types.AaObjectAttributeSection(
        header=header,
        count=count,
        attributes=attrs
    ))

    # InputExtension?
    primitives._seek_forward(input=input, length=18) # inherited input extension?
    primitives._seek_forward(input=input, length=646)
    primitives._seek_forward(input=input, length=20)
    primitives._seek_string(input=input) #inputextension
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20)
    test = primitives._seek_string(input=input) # parent template name?
    primitives._seek_forward(input=input, length=596)
    header = primitives._seek_bytes(input=input, length=16)
    count = primitives._seek_int(input=input)
    attrs = []
    if count > 0:
        for i in range(count):
            attrs.append(_get_attr_type1(input=input))
    primitives._seek_end_section(input=input)
    sections.append(types.AaObjectAttributeSection(
        header=header,
        count=count,
        attributes=attrs
    ))

    # Then there seem to be four NoneType objects
    for i in range(4): primitives._seek_object_value(input=input)

    header = None
    count = primitives._seek_int(input=input)
    attrs = []
    if count > 0:
        for i in range(count):
            attrs.append(_get_attr_type2(input=input))
    sections.append(types.AaObjectAttributeSection(
        header=header,
        count=count,
        attributes=attrs
    ))

    return types.AaObjectContent(
        main_section_id=main_section_id,
        template_name=template_name,
        attr_sections=sections
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