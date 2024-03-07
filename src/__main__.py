from pathlib import Path
from .services import GamecubeImageReader

if __name__ == "__main__":
    path = Path("/home/mike/Downloads/")
    ir = GamecubeImageReader(path.joinpath("PokemonColosseum.iso"))

    print(ir.table_of_contents)

    fsys = ir.extract_file("common.fsys")

    with path.joinpath("ExtractedGames").joinpath("test_common.fsys").open('wb') as fsys_file:
        fsys_file.write(fsys.contents.stream)



