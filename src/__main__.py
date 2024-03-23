import argparse
import asyncio
from mmap import ACCESS_READ, mmap
from pathlib import Path

from tqdm import tqdm
from src.definitions import MMapStream, AbstractFileArchive
from src.definitions.gamecube import GamecubeISO

def cmdline_args():
        # Make parser object
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument("input_image_path",
                   help="Path to the gamecube disc image.", type=Path)
    p.add_argument("action", type=str, choices=['extract', 'save'], default='extract',
                   help="One of 'extract', 'save' (default: %(default)s)")
    p.add_argument("--with_system_files", action="store_true",
                   help="If true, and action is extract, save the system file images as well.")
    p.add_argument("--defragment", action="store_true",
                   help="If true, update the image to remove junk data.")
    p.add_argument("-o", "--output", type=Path,
                   help="increase output verbosity (default: %(default)s)")
                   

    return p.parse_args()



async def extract_file(output: Path, filename: str, image_reader: AbstractFileArchive):
    file = image_reader._extract_file(filename)
    with output.joinpath(file.file_name).open('wb') as outfile:
        outfile.write(file.to_bytes())

async def extract_files(args):
    fst_file_list = ir.table_of_contents.get_fst_file_list()
    for file in tqdm(fst_file_list):
        await extract_file(args.output, file, ir)

if __name__ == "__main__":
    args = cmdline_args()
    in_path = Path(args.input_image_path)
    out_path = Path(args.output)
    with in_path.open("rb") as in_file:
        mmap_stream = mmap(in_file.fileno(), 0, access=ACCESS_READ)
        ir = GamecubeISO(in_path.name, MMapStream(mmap_stream))

    if args.defragment:
        system_file_size = ir.get_system_size()
        ir.table_of_contents.defragment(system_file_size)

    if args.action == 'extract':
        asyncio.run(extract_files(args))
            
    elif args.action == 'save':
        ir.save_to_disk(out_path)
