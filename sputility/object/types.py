from dataclasses import dataclass, field
from datetime import datetime, timedelta

from . import enums

@dataclass
class AaBinStream:
    data: bytes
    offset: int

@dataclass
class AaObjectHeader:
    base_gobjectid: int
    is_template: bool       # <Obj>._IsTemplate
    this_gobjectid: int
    security_group: str     # <Obj>.SecurityGroup
    parent_gobjectid: int
    tagname: str            # <Obj>.Tagname
    contained_name: str     # <Obj>.ContainedName
    config_version: int     # <Obj>.ConfigVersion
    hierarchal_name: str    # <Obj>.HierarchalName
    host_name: str          # <Obj>.Host
    container_name: str     # <Obj>.Container
    area_name: str          # <Obj>.Area
    derived_from: str
    based_on: str           # <Obj>._BasedOn
    galaxy_name: str

@dataclass
class AaReference:
    unk01: bytes
    refA: str
    refB: str

@dataclass
class AaQualifiedEnum:
    value: str
    ordinal: int
    primitive_id: bytes
    attribute_id: bytes

@dataclass
class AaObjectValue:
    header: bytes = field(repr=False)
    datatype: enums.AaDataType
    value: bytes | bool | int | float | str | datetime | timedelta | list | AaReference | AaQualifiedEnum

@dataclass
class AaObjectAttribute:
    id: int
    name: str
    attr_type: enums.AaDataType
    array: bool
    permission: enums.AaPermission
    write: enums.AaWriteability
    locked: enums.AaLocked
    parent_gobjectid: int
    parent_name: str
    source: enums.AaSource
    value: AaObjectValue
    primitive_name: str

@dataclass
class AaObjectAttributeSection:
    header: bytes
    count: int
    attributes: list[AaObjectAttribute]

@dataclass
class AaObjectExtension:
    extension_type: enums.AaExtension
    instance_name: str
    extension_name: str
    primitive_name: str
    parent_name: str
    attributes: list[AaObjectAttribute]
    messages: list[AaObjectValue]

@dataclass
class AaObjectContent:
    main_section_id: int
    template_name: str
    attr_sections: list[AaObjectAttributeSection]
    extensions: list[AaObjectExtension]
    codebase: str           # <Obj>.CodeBase

@dataclass
class AaObject:
    size: int
    offset: int
    header: AaObjectHeader
    content: AaObjectContent