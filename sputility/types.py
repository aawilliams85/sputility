from dataclasses import dataclass, field

@dataclass
class AAArchive:
    name: str
    data: bytes
    path: list[str]
    size: int

@dataclass
class AAManifestIOMap:
    filename: str

@dataclass
class AAManifestTemplate:
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
    derived_templates: list['AAManifestTemplate'] = field(default_factory=list)
    derived_instances: list['str'] = field(default_factory=list)

@dataclass
class AAManifestVersion:
    cdi_version: str
    ias_version: str

@dataclass
class AAManifest:
    product_version: AAManifestVersion
    templates: list[AAManifestTemplate]
    bindings: AAManifestIOMap
    object_count: int