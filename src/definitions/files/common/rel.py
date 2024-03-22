from ... import AbstractFile


class REL(AbstractFile):
    """
    This class provides a wrapper around REL files.
    REL files are execucutable and relocatable modules called into by the main DOL.
    They are essentially libraries for the game.
    """
