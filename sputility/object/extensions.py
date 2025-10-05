import pprint

from . import attributes
from . import enums
from . import primitives
from . import types

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

def get_extension(input: types.AaBinStream) -> types.AaObjectExtension:
    print('>>>> START EXTENSION >>>>')
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    section_type = primitives._seek_int(input=input)
    section_name = primitives._seek_string(input=input)
    print(f'>>>>>>>> NAME {section_name}')
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    extension_name = primitives._seek_string(input=input)
    primitive_name = _get_primitive_name(section_name=section_name, extension_name=extension_name)
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    parent_name = primitives._seek_string(input=input) # this object or parent inherited from
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=16) # header?
    attr_count = primitives._seek_int(input=input)
    attrs = []
    if attr_count > 0:
        for i in range(attr_count):
            attr = attributes.get_attr_type1(input=input)
            attr.name = _get_attribute_fullname(section_name=section_name, attribute_name=attr.name)
            attr.primitive_name = primitive_name
            attrs.append(attr)
            #pprint.pprint(attr)
    primitives._seek_end_section(input=input)

    # ???
    while primitives._lookahead_pattern(input=input, pattern=primitives.PATTERN_OBJECT_VALUE):
        primitives._seek_object_value(input=input) # 1,2,4 unknown.  3 is a message queue for warnings from this section+extension?

    attr_count = primitives._seek_int(input=input)
    if attr_count > 0:
        for i in range(attr_count):
            attr = attributes.get_attr_type2(input=input)
            attr.name = _get_attribute_fullname(section_name=section_name, attribute_name=attr.name)
            attr.primitive_name = primitive_name
            attrs.append(attr)
            #pprint.pprint(attr)
    #primitives._seek_end_section(input=input)

    #pprint.pprint(attrs)
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    print('>>>> END EXTENSION >>>>')
    
    return types.AaObjectExtension(
        section_type=enums.AaExtension(section_type),
        section_name=section_name,
        extension_name=extension_name,
        primitive_name=primitive_name,
        parent_name=parent_name,
        attributes=attrs
    )