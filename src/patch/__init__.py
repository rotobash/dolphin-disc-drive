
import bsdiff4
from pathlib import Path
from zipfile import ZipFile
from ..gamecube import GamecubeFileFactory
from .. import GamecubeISO, AbstractFileArchive, MMapStream, SystemCodes

def patch(patch_file_path: Path, rom_file_path: Path, patched_rom_file_path: Path):
    with patch_file_path.open('r') as patch_file:
        with ZipFile(patch_file) as patch_archive:
            game_archive: AbstractFileArchive = None
            syscode = patch_archive.read("SYSCODE")[0]
            if syscode == SystemCodes.Gamecube:
                game_archive = GamecubeISO.open_image_file(rom_file_path)
            
            for file_name in patch_archive.namelist():
                if file_name.endswith("patch"):
                    original_file_name = file_name.rsplit(".", 1)[0]
                    file_patch = patch_archive.read(file_name)
                    file = game_archive.open_file(original_file_name)
                    patched_file = bsdiff4.patch(file, file_patch)
                    # todo: another layer of factories
                    new_file = GamecubeFileFactory.read_file(original_file_name, patched_file)
                    game_archive.replace_file(new_file)

    with MMapStream.from_file(patched_rom_file_path) as patched_rom:
        game_archive.build_archive(patched_rom)

