from mmap import mmap, ACCESS_WRITE
from pathlib import Path

from src.definitions.stream import MMapStream
from .services import GamecubeImageReader


if __name__ == "__main__":
    path = Path("H:\ISO\ExtractedGames")
    ir = GamecubeImageReader(path.joinpath("Pokemon Colosseum.iso"))

    file_size = ir.get_image_size()
    ir.table_of_contents.defragment(ir.get_system_size())
    with path.joinpath("repack.iso").open("w+") as iso:
        fileno = iso.fileno()
        with mmap(fileno, length=1459978240, access=ACCESS_WRITE) as iso_mmap:
            iso_stream = MMapStream(iso_mmap)
            ir.build_image(iso_stream)
