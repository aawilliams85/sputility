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
class AaObjectValue:
    header: bytes
    datatype: enums.AaDataType
    value: bool | int | float | str | datetime | timedelta | list

@dataclass
class AaObjectAttribute:
    name: str
    attr_type: enums.AaDataType
    array: bool
    permission: enums.AaPermission
    write: enums.AaWriteability
    locked: bool
    parent_gobjectid: int
    parent_name: str
    value_type: enums.AaDataType
    value: bool | int | float | str | datetime | timedelta | list

@dataclass
class AaObjectContent:
    main_section_id: int
    template_name: str
    attr_section_id: int
    attr_count: int
    attr_section: list[AaObjectAttribute]
    short_desc: str         # <Obj>.ShortDesc

@dataclass
class AaObject:
    header: AaObjectHeader
    content: AaObjectContent