import json
from dataclasses import asdict
import os
import pprint

from . import attributes
from . import enums
from . import primitives
from . import types

PRINT_DEBUG_INFO = True

def _get_header(input: types.AaBinStream) -> types.AaObjectHeader:
    if PRINT_DEBUG_INFO: print(f'>>>> START HEADER - OFFSET {input.offset:0X} >>>>')
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
    primitives._seek_forward(input=input, length=524)

    # Some versions have an extra block here
    if not(primitives._lookahead_pattern(input=input, pattern=primitives.PATTERN_END_OF_HEADER)):
        unk01 = primitives._seek_int(input=input)
        primitives._seek_forward(input=input, length=660)
    else:
        unk01 = primitives._seek_forward(input=input, length=4)

    galaxy_name = primitives._seek_string_var_len(input=input)

    # Some versions have a NoneType block here
    if (primitives._lookahead_pattern(input=input, pattern=primitives.PATTERN_OBJECT_VALUE)):
        unk02 = primitives._seek_object_value(input=input)
        primitives._seek_end_section(input=input)

    # Trying to figure out whether this first
    # byte being inserted means it is a template.
    #
    # Instances seem to be one byte shorter in this section.
    is_instance = primitives._seek_bool(input=input)
    if not(is_instance): primitives._seek_bool(input=input)

    if PRINT_DEBUG_INFO: print(f'>>>> END HEADER - OFFSET {input.offset:0X} >>>>')
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
        galaxy_name=galaxy_name,
        code_base=None
    )

def _get_attribute_fullname(section_name: str, attribute_name: str) -> str:
    if (attribute_name is not None) and (section_name is not None):
        if (len(section_name) > 0):
            return f'{section_name}.{attribute_name}'
    return attribute_name

def _get_primitive_name(section_name: str, extension_name: str) -> str:
    # Typically this is <Section>_<Extension>.
    # But some builtins don't show up with a name... is it UserDefined or maybe always the name of the codebase?
    if (section_name is not None) and (extension_name is not None):
        if (len(section_name) > 0):
            return f'{section_name}_{extension_name}'
    return ''

def _get_extension(input: types.AaBinStream) -> types.AaObjectExtension:
    if PRINT_DEBUG_INFO: print(f'>>>> START EXTENSION - OFFSET {input.offset:0X} >>>>')
    instance_id = primitives._seek_int(input=input)
    instance_name = primitives._seek_string(input=input)
    if PRINT_DEBUG_INFO: print(f'>>>>>>>> INSTANCE ID: {instance_id:0X}, INSTANCE NAME: {instance_name}')
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    extension_name = primitives._seek_string(input=input)
    primitive_name = _get_primitive_name(section_name=instance_name, extension_name=extension_name)
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    parent_name = primitives._seek_string(input=input) # this object or parent inherited from
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=16) # header?
    attr_count = primitives._seek_int(input=input)
    attrs = []
    if attr_count > 0:
        for i in range(attr_count):
            if PRINT_DEBUG_INFO: print(f'>>>>>>>> START ATTR - OFFSET {input.offset:0X} >>>>')
            attr = attributes.get_attr_type1(input=input)
            attr.name = _get_attribute_fullname(section_name=instance_name, attribute_name=attr.name)
            attr.primitive_name = primitive_name
            attrs.append(attr)
    primitives._seek_end_section(input=input)

    # Message queues for this extension?
    # 1 - Object errors
    # 2 - Symbol warnings
    # 3 - Object warnings
    # 4 - ???
    messages = []
    for i in range(4):
        messages.append(primitives._seek_object_value(input=input))

    attr_count = primitives._seek_int(input=input)
    if attr_count > 0:
        for i in range(attr_count):
            if PRINT_DEBUG_INFO: print(f'>>>>>>>> START ATTR - OFFSET {input.offset:0X} >>>>')
            attr = attributes.get_attr_type2(input=input)
            attr.name = _get_attribute_fullname(section_name=instance_name, attribute_name=attr.name)
            attr.primitive_name = primitive_name
            attrs.append(attr)

    #print(f'Instance Name: {instance_name}, Extension Type: {extension_type}, Extension Name: {extension_name}, Type: {enums.AaExtension(extension_type).name}')
    if PRINT_DEBUG_INFO: print(f'>>>> END EXTENSION - OFFSET {input.offset:0X} >>>>')
    return types.AaObjectExtension(
        instance_id=instance_id,
        instance_name=instance_name,
        extension_name=extension_name,
        primitive_name=primitive_name,
        parent_name=parent_name,
        attributes=attrs,
        messages=messages
    )

def deserialize_aaobject(input: str| bytes) -> types.AaObject:
    # Read in object from memory or from file.
    #
    # On disk this should be a *.txt file extracted
    # from an *.aapkg file.
    data: bytes
    if isinstance(input, (str, os.PathLike)):
        try:
            with open(input, 'rb') as file:
                data = file.read()
        except:
            pass
    elif isinstance(input, bytes):
        data = bytes(input)
    else:
        raise TypeError('Input must be a file path (str/PathLike) or bytes.')

    # Use this binary stream to aid with decoding
    # so that the data can be parsed through
    obj = types.AaBinStream(
        data=data,
        offset=0
    )

    # Deserialize content
    header = _get_header(input=obj)
    extension_count = primitives._seek_int(input=obj)
    extensions = []
    for i in range(extension_count):
        extensions.append(_get_extension(input=obj))

    # After all extensions are over - templates have
    # more content that is mostly not reviewed yet.
    if header.is_template:
        primitives._seek_forward(input=obj, length=1)

        # GUID sections???
        guid1 = primitives._seek_string(input=obj, length=512)
        guid2 = primitives._seek_string(input=obj, length=512)

        # Codebase ???
        primitives._seek_forward(input=obj, length=36)
        header.code_base = primitives._seek_string(input=obj)

    # Return structures object
    return types.AaObject(
        size=len(obj.data),
        offset=obj.offset,
        header=header,
        extensions=extensions
    )

def explode_aaobject(
    input: str | bytes,
    output_path: str
) -> types.AaObject:
    # Create output folder if it doesn't exist yet
    if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)

    obj = deserialize_aaobject(input)
    object_path = os.path.join(output_path, obj.header.tagname)
    os.makedirs(object_path, exist_ok=True)

    # Object header info
    header_path = os.path.join(object_path, 'header.json')
    with open(header_path, 'w') as f:
        f.write(json.dumps(asdict(obj.header), indent=4))

    # Object extensions
    for ext in obj.extensions:
        ext_path = os.path.join(object_path, 'extensions', enums.AaExtension(ext.instance_id).name)
        ext_file = os.path.join(ext_path, f'{ext.primitive_name}.json')
        os.makedirs(ext_path, exist_ok=True)
        with open(ext_file, 'w') as f:
            f.write(json.dumps(asdict(ext), indent=4, default=str))

        # Special handling for Script extensions to dump
        # body of script to a more immediately useful place.
        #
        # Maybe the concept should be to dump all of the raw
        # extensions to one place and useful formatted info
        # to another?
        if ext.instance_id == enums.AaExtension.Script.value:
            for attr in ext.attributes:
                if (attr.id == 100):
                    script_file = os.path.join(ext_path, f'{ext.instance_name}.txt')
                    with open(script_file, 'w') as f:
                        f.write(attr.value.value)

    return obj