# dolphin-disc-drive

A set of tools to work with the gamecube disc's filesystem.

## Roadmap

This tool is WIP at the current time.

1. ~Read the disc filesystem, extract the system files, and use the table of contents to extract files from the image.~
2. ~Add/Replace/Remove files from the FST while keeping the file offsets + sizes valid~
3. Build a patch from the original file to apply any changes.
4. Implement tests

-- Release Candidate published to pip, new release for each point

5. Implement DOL patching fully (i.e. adding/removing data)
6. Add file type wrappers for common files like REL/ARC/BMP etc. (if there's documentation and not wildly different between versions)

-- Full release

7. Add compression services for common methods like ZIP/LZSS
8. Add support for image file types other than ISO

## Installation

Run `pip install dolphin-disc-drive`
Requires Python 3.8 or higher

## Usage

This library can be used via a command line interface or imported as library from another Python project.

### CLI

`dolphin-disc-drive [-h] [--with_system_files] [--defragment] [-o OUTPUT] input_image_path {extract,save}`

TODO: explain options

### Library

Reading a Gamecube image file and extracting files:

```python
from dolphin_disc_drive import GamecubeISO, MemoryStream
in_path = Path(args.input_image_path)
iso = GamecubeISO.open_image_file(in_path)

# file is AbstractFile, depending on type we can work with it further
# Any changes to opened files will be automatically detected and processed when re-saving the image.
file = iso.open_file("file name")

# if you want to work with the image as a whole
mem_stream = MemoryStream()
image = iso.build_image(mem_stream)
# note: using an empty MemoryStream is slow for large files because it has to allocate memory as it builds the file.
# consider an MMapStream (file backed) or pre-allocating enough space in the MemoryStream

# if you want to save the image to disk
iso.save_to_disk("output path")
```

To implement a custom file type that can be extracted from the filesystem:

```python
from dolphin_disc_drive import AbstractFile, GamecubeFileFactory

class MyCustomFile(AbstractFile):
    pass

# note: file extension should contain the '.' and MyCustomFile is not instantiated
GamecubeFileFactory.register_file(".extension", MyCustomFile)

file: MyCustomFile = GamecubeFileFactory.read_file(".extension", file_stream)
```

To implement a custom compression algorithm that can be used on files:

```python
from dolphin_disc_drive import AbstractFile
from dolphin_disc_drive.services import CompressionService, CompressionServiceFactory

class MyCustomCompressionService(CompressionService):
    def compress(self, file: AbstractFile):
        pass

    def decompress(self, file: AbstractFile):
        pass

CompressionServiceFactory.register_compression_method("compression method", MyCustomCompressionService())
f = CompressionServiceFactory.decompress(file)
x = CompressionServiceFactory.compress(f)


# similar for encryption
```
