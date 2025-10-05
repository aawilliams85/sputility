import os

from . import attributes
from . import extensions
from . import primitives
from . import types

def _get_header(input: types.AaBinStream) -> types.AaObjectHeader:
    print('>>>> START HEADER >>>>')
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
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

    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    print('>>>> END HEADER >>>>')
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

def _get_content(input: types.AaBinStream) -> types.AaObjectContent:
    print('>>>> START CONTENT >>>>')
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
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
            attrs.append(attributes.get_attr_type1(input=input))
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
            attrs.append(attributes.get_attr_type2(input=input))
    sections.append(types.AaObjectAttributeSection(
        header=header,
        count=count,
        attributes=attrs
    ))

    exts = []
    while primitives._lookahead_extension(input=input):
        exts.append(extensions.get_extension(input=input))

    # Don't yet know how to tell if this will be present.
    # Only templates?
    '''
    # GUID sections???
    guid1 = primitives._seek_bytes(input=input, length=512)
    guid2 = primitives._seek_bytes(input=input, length=512)

    # Codebase ???
    primitives._seek_forward(input=input, length=36)
    codebase = primitives._seek_string(input=input)

    # Where did we leave off with the source file that hasn't been decoded yet
    print(f'>>>>>>>> OFFSET {input.offset:0X}')
    print('>>>> END CONTENT >>>>')
    '''

    return types.AaObjectContent(
        main_section_id=main_section_id,
        template_name=template_name,
        attr_sections=sections,
        extensions=exts,
        codebase=None
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
        size=len(aaobj.data),
        offset=aaobj.offset,
        header=header,
        content=content
    )