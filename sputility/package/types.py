from dataclasses import dataclass, field

@dataclass
class AaArchive:
    name: str
    data: bytes
    path: list[str]
    size: int

@dataclass
class AaManifestIODeviceMap:
    filename: str

@dataclass
class AaManifestInstance:
    tag_name: str
    gobjectid: int
    file_name: str
    config_version: int
    codebase: str
    security_group: str
    host_name: str
    area_name: str
    cont_name: str
    toolset_name: str

@dataclass
class AaManifestTemplate:
    tag_name: str
    gobjectid: int
    file_name: str
    config_version: int
    codebase: str
    security_group: str
    host_name: str
    area_name: str
    cont_name: str
    toolset_name: str
    is_protected: bool
    derived_templates: list['AaManifestTemplate'] = field(default_factory=list)
    derived_instances: list[AaManifestInstance] = field(default_factory=list)

@dataclass
class AaManifestVersion:
    cdi_version: str
    ias_version: str

@dataclass
class AaManifest:
    product_version: AaManifestVersion
    templates: list[AaManifestTemplate]
    bindings: AaManifestIODeviceMap
    object_count: int