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
    code_base: str          # <Obj>.CodeBase

@dataclass
class AaReference:
    refA: str
    refB: str

@dataclass
class AaQualifiedEnum:
    value: str
    ordinal: int
    primitive_id: int
    attribute_id: int

@dataclass
class AaQualifiedStruct:
    unk01: int
    unk02: int
    unk03: int
    unk04: int
    unk05: int

@dataclass
class AaObjectValue:
    datatype: enums.AaDataType
    value: bool | int | float | str | datetime | timedelta | list | AaReference | AaQualifiedEnum

@dataclass
class AaObjectAttribute:
    offset: int
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
class AaObjectExtension:
    instance_id: int
    instance_name: str
    extension_name: str
    primitive_name: str
    parent_name: str
    attributes: list[AaObjectAttribute]
    messages: list[AaObjectValue]

    def get_attribute(self, attribute_id: int):
        return next((attr for attr in self.attributes if attr.id == attribute_id), None)

@dataclass
class AaObject:
    size: int
    offset: int
    header: AaObjectHeader
    extensions: list[AaObjectExtension]

@dataclass
class AaScriptHeader:
    name: str
    primitive_name: str
    expression: str
    trigger_type: enums.AaScriptTriggerType
    trigger_period: timedelta
    trigger_quality_changes: bool
    trigger_deadband: float
    asynchronous_execution: bool
    asynchronous_timeout_ms: int
    historize_state: bool
    alarm_enable: bool

@dataclass
class AaScriptContent:
    aliases: list[str, str]
    declarations: str
    body_text_execute: str
    body_text_startup: str
    body_text_shutdown: str
    body_text_onscan: str
    body_text_offscan: str
    
@dataclass
class AaScript:
    header: AaScriptHeader
    content: AaScriptContent