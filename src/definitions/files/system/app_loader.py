from ... import MemoryStream, AbstractFile


class AppLoader(AbstractFile):
    def __init__(self, app_loader: MemoryStream) -> None:
        super().__init__("appldr.bin", app_loader)
