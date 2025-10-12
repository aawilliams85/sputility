import io
import os
from typing import List
import xml.etree.ElementTree as ET
import zipfile

from . import types

def _path_to_list(path: str, insensitive: bool = True) -> list[str]:
    path = path.replace('\\', '/')
    if insensitive: path = path.casefold()
    components = [comp for comp in path.split('/') if comp]
    return components if components else [path]

def _create_subfolders(output_path: str, archive_paths: list[str]):
    folders = archive_paths[:-1]
    current_path = output_path
    for folder in folders:
        current_path = os.path.join(current_path, folder)
        os.makedirs(current_path, exist_ok=True)
    return os.path.join(current_path, archive_paths[-1])

def _get_manifest_instances(element: ET.Element) -> types.AaManifestInstance:
    return types.AaManifestInstance(
        tag_name=element.attrib.get('tag_name', ''),
        gobjectid=int(element.attrib.get('gobjectid', '0')),
        file_name=element.attrib.get('file_name', ''),
        config_version=int(element.attrib.get('config_version', '0')),
        codebase=element.attrib.get('codebase', ''),
        security_group=element.attrib.get('security_group', ''),
        host_name=element.attrib.get('host_name', ''),
        area_name=element.attrib.get('area_name', ''),
        cont_name=element.attrib.get('cont_name', ''),
        toolset_name=element.attrib.get('toolset_name', '')
    )

def _get_manifest_templates(element: ET.Element) -> types.AaManifestTemplate:
    # Extract attributes
    attrs = {
        'tag_name': element.get('tag_name', ''),
        'gobjectid': int(element.get('gobjectid', '')),
        'file_name': element.get('file_name', ''),
        'config_version': int(element.get('config_version', '')),
        'codebase': element.get('codebase', ''),
        'security_group': element.get('security_group', ''),
        'host_name': element.get('host_name', ''),
        'area_name': element.get('area_name', ''),
        'cont_name': element.get('cont_name', ''),
        'toolset_name': element.get('toolset_name', ''),
        'is_protected': bool(int(element.get('is_protected', '0')))
    }

    # Recursively parse derived_templates
    derived_templates = []
    dt_element = element.find('derived_templates')
    if dt_element is not None:
        for child in dt_element.findall('template'):
            derived_templates.append(_get_manifest_templates(child))

    # Placeholder for derived_instances
    derived_instances = []
    di_element = element.find('derived_instances')
    if di_element is not None:
        for inst in di_element.findall('instance'):
            derived_instances.append(_get_manifest_instances(inst))

    return types.AaManifestTemplate(**attrs, derived_templates=derived_templates, derived_instances=derived_instances)

def _print_manifest_template(template: types.AaManifestTemplate, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}- Template: {template.tag_name} (ID: {template.gobjectid}, File: {template.file_name})")

    # Print derived instances if any (currently placeholders)
    if template.derived_instances:
        for instance in template.derived_instances:
            print(f"{prefix}  * Instance: {instance}")

    # Recursively print derived templates
    for child in template.derived_templates:
        _print_manifest_template(child, indent + 1)

def _get_stream_by_name(
    streams: list[types.AaArchive], 
    name: str, 
    case_insensitive: bool
) -> types.AaArchive:
    if case_insensitive:
        return next(x for x in streams if x.name.casefold() == name.casefold())
    else:
        return next(x for x in streams if x.name == name)

def _get_manifest(
    streams: list[types.AaArchive],
) -> types.AaManifest:
    stream = _get_stream_by_name(streams, 'Manifest.xml', case_insensitive=False)
    root = ET.fromstring(stream.data.decode('utf-8'))

    version = types.AaManifestVersion('','')
    for version_elem in root.findall('product_version'):
        version = types.AaManifestVersion(
            cdi_version=version_elem.get('cdiversion', ''),
            ias_version=version_elem.get('iasversion', '')
        )

    templates = []
    for template_elem in root.findall('template'):
        templates.append(_get_manifest_templates(template_elem))

    bindings = types.AaManifestIODeviceMap('')
    for bindings_elem in root.findall('IODeviceMap'):
        bindings = types.AaManifestIODeviceMap(
            filename=bindings_elem.get('filename', '')
        )

    object_count = 0
    for object_count_elem in root.findall('TotalObjectCount'):
        object_count = int(object_count_elem.get('objectcount', ''))

    manifest = types.AaManifest(
        product_version=version,
        templates=templates,
        bindings=bindings,
        object_count=object_count
    )
    return manifest

def decompress_cab(
    file: zipfile.ZipFile,
    prefix: str
) -> list[types.AaArchive]:
    streams: list[types.AaArchive] = []
    for info in file.infolist():
        if info.is_dir():
            continue
        data = file.read(info.filename)
        file_path = f'{prefix}/{info.filename}'
        file_path_list = _path_to_list(path=file_path, insensitive=False)
        streams.append(types.AaArchive(
            name=file_path_list[-1],
            data=data,
            path=file_path_list,
            size=len(data)
        ))
    return streams

def decompress_aapkg(
    file: zipfile.ZipFile
) -> list[types.AaArchive]:
    streams: list[types.AaArchive] = []
    file_name, file_ext = os.path.splitext(str(file.filename))
    for stream_path in file.namelist():
        with io.BytesIO(file.read(stream_path)) as package_bytes:
            with zipfile.ZipFile(package_bytes) as cab_zip:
                cab_prefix = f'{os.path.basename(file_name)}/{stream_path}'
                streams.extend(decompress_cab(file=cab_zip,prefix=cab_prefix))
    return streams
    
def aapkg_to_memory(
    input_path: str,
) -> tuple[types.AaManifest, list[types.AaArchive]]:
    # Directly dump archive with no application-specific
    # handling.
    with zipfile.ZipFile(input_path, 'r') as archive:
        streams = decompress_aapkg(file=archive)
        manifest = _get_manifest(streams)
        return (manifest, streams)

def aapkg_to_folder(
    input_path: str,
    output_path: str
) -> types.AaManifest:
    # Directly dump archive with no application-specific
    # handling.

    # Create output folder if it doesn't exist yet
    if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)

    with zipfile.ZipFile(input_path, 'r') as archive:
        streams = decompress_aapkg(file=archive)
        manifest = _get_manifest(streams)
        for stream in streams:
            stream_output_path = _create_subfolders(output_path, stream.path)
            with open(stream_output_path, 'wb') as f:
                f.write(stream.data)

        return manifest