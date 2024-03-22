# dolphin-disc-drive
A set of tools to work with the gamecube disc's filesystem.

## Roadmap
This tool is WIP at the current time.

1. ~Read the disc filesystem, extract the system files, and use the table of contents to extract files from the image.~
2. Add/Replace/Remove files from the FST while keeping the file offsets + sizes valid
3. Build a patch from the original file to apply any changes.
4. Implement tests

-- Release Candidate published to pip, new release for each point

5. Implement DOL patching fully (i.e. adding/removing data)
6. Add file type wrappers for common files like REL/ARC/BMP etc. (if there's documentation and not wildly different between versions)

-- Full release

7. Add compression services for common methods like ZIP/LZSS
8. Add support for image file types other than ISO
