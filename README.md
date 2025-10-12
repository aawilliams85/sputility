# sputility

sputility is a Python tool to interface with System Platform packages (*.aapkg).<br>
It's all preliminary guesswork and likely to change.  Use at your own risk.<br>

## Capabilities

The public classes in sputility provide the following capabilities:

> ### SPUtility
>
> SPUtility provides the following standard functions:
> - Decompress package (extract files from *.aaPKG to disk)
> - Deserialize package (extract files from *.aaPKG to memory, deserialize individual object *.txt files to disk)
> - Deserialize object (deserialize specific object *.txt file to disk)

## Getting Started

### Installation

To install from pip, run the following command:
```console
pip install sputility
```

To upgrade to the latest release:
```console
pip install sputility --upgrade
```

### Example

```python
from sputility import SPUtility
spu = SPUtility()
spu.deserialize_package(
    input_path='YourAaPkgFile', 
    output_path='YourFolder', 
    progress=None
)
```

## Contributing

Contributions welcome!<br>
Ideas, code, hardware testing, bug reports, etc.<br>