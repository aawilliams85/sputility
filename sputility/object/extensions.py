import pprint

from . import attributes
from . import enums
from . import primitives
from . import types

def get_section_inputextension(input: types.AaBinStream) -> bytes:
    print('>>>> START INPUTEXTENSION >>>>')
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    section_type = primitives._seek_int(input=input)
    section_name = primitives._seek_string(input=input)
    print(f'>>>>>>>> NAME {section_name}')
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    extension_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    object_name = primitives._seek_string(input=input) # this object or parent inherited from
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=16) # header?
    attr_count = primitives._seek_int(input=input)
    attrs = []
    if attr_count > 0:
        for i in range(attr_count):
            attr = attributes.get_attr_type1(input=input)
            attr.name = f'{section_name}.{attr.name}'
            attr.primitive_name = f'{section_name}_{extension_name}'
            attrs.append(attr)
    primitives._seek_end_section(input=input)

    # ???
    while primitives._lookahead_pattern(input=input, pattern=primitives.PATTERN_OBJECT_VALUE):
        primitives._seek_object_value(input=input) # 1,2,4 unknown.  3 is a message queue for warnings from this section+extension?

    attr_count = primitives._seek_int(input=input)
    if attr_count > 0:
        for i in range(attr_count):
            attr = attributes.get_attr_type2(input=input)
            #attr.name = f'{section_name}.{attr.name}'
            #attr.primitive_name = f'{section_name}_{extension_name}'
            attrs.append(attr)
            #pprint.pprint(attr)
    #primitives._seek_end_section(input=input)

    #pprint.pprint(attrs)
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    print('>>>> END INPUTEXTENSION >>>>')

def get_section_scriptextension(input: types.AaBinStream) -> bytes:
    print('>>>> START SCRIPTEXTENSION >>>>')
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    section_type = primitives._seek_int(input=input)
    section_name = primitives._seek_string(input=input)
    print(f'>>>>>>>> NAME {section_name}')
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    extension_name = primitives._seek_string(input=input)
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=20) # header?
    object_name = primitives._seek_string(input=input) # this object or parent inherited from
    primitives._seek_forward(input=input, length=596)
    primitives._seek_forward(input=input, length=16) # header?
    primitives._seek_forward(input=input, length=12)

    # ???
    while primitives._lookahead_pattern(input=input, pattern=primitives.PATTERN_OBJECT_VALUE):
        primitives._seek_object_value(input=input) # 1,2,4 unknown.  3 is a message queue for warnings from this section+extension?

    attr_count = primitives._seek_int(input=input)
    attrs = []
    if attr_count > 0:
        for i in range(attr_count):
            attrs.append(attributes.get_attr_type2(input=input))

    #pprint.pprint(attrs)
    #print(len(attrs))
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    print('>>>> END SCRIPTEXTENSION >>>>')
