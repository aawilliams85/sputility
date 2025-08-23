from dataclasses import dataclass
import zipfile
import io
import os

@dataclass
class AAArchive:
    name: str
    data: bytes
    path: list[str]
    size: int

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

def decompress_cab(
    file: zipfile.ZipFile,
    prefix: str
) -> list[AAArchive]:
    streams: list[AAArchive] = []
    for info in file.infolist():
        if info.is_dir():
            continue
        data = file.read(info.filename)
        file_path = f'{prefix}/{info.filename}'
        file_path_list = _path_to_list(path=file_path, insensitive=False)
        streams.append(AAArchive(
            name=file_path_list[-1],
            data=data,
            path=file_path_list,
            size=len(data)
        ))
    for stream in streams:
        print(stream.name)
    return streams

def decompress_aapkg(
    file: zipfile.ZipFile
) -> list[AAArchive]:
    streams: list[AAArchive] = []
    file_name, file_ext = os.path.splitext(str(file.filename))
    for stream_path in file.namelist():
        with io.BytesIO(file.read(stream_path)) as package_bytes:
            with zipfile.ZipFile(package_bytes) as cab_zip:
                cab_prefix = f'{os.path.basename(file_name)}/{stream_path}'
                print(cab_prefix)
                streams.extend(decompress_cab(file=cab_zip,prefix=cab_prefix))
    return streams
    
def archive_to_disk(
    file_path: str,
    output_path: str
):
    # Directly dump archive with no application-specific
    # handling.

    # Create output folder if it doesn't exist yet
    if not(os.path.exists(output_path)): os.makedirs(output_path, exist_ok=True)

    with zipfile.ZipFile(file_path, 'r') as archive:
        streams = decompress_aapkg(file=archive)
        for stream in streams:
            stream_output_path = _create_subfolders(output_path, stream.path)
            with open(stream_output_path, 'wb') as f:
                f.write(stream.data)