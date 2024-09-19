import os
import shutil
from ignis.utils import Utils
from gi.repository import GObject  # type: ignore
from ignis.services.options import OptionsService
from ignis.base_service import BaseService
from .window import WallpaperLayerWindow
from .constants import CACHE_WALLPAPER_PATH
from .options import GROUP_NAME, WALLPAPER_PATH_OPTION

class WallpaperService(BaseService):
    """
    A simple service to set the wallpaper.
    Supports multiple monitors.

    Properties:
        - **wallpaper** (``str``, read-write): The path to the image.

    **Example usage:**

    .. code-block:: python

        .. code-block:: python

        from ignis.services.wallpaper import WallpaperService

        wallpaper = WallpaperService.get_default()

        wallpaper.set_wallpaper("path/to/image")

    """

    def __init__(self):
        super().__init__()
        self._windows: list[WallpaperLayerWindow] = []

        options = OptionsService.get_default()

        self._opt_group = options.create_group(name=GROUP_NAME, exists_ok=True)
        self._opt_group.create_option(name=WALLPAPER_PATH_OPTION, default=None, exists_ok=True)

        self.__sync()

    @GObject.Property
    def wallpaper(self) -> str:
        return self._opt_group.get_option(WALLPAPER_PATH_OPTION)

    @wallpaper.setter
    def wallpaper(self, value: str) -> None:
        try:
            shutil.copy(value, CACHE_WALLPAPER_PATH)
        except shutil.SameFileError:
            return

        self._opt_group.set_option(WALLPAPER_PATH_OPTION, value)
        self.__sync()

    def __sync(self) -> None:
        for i in self._windows:
            i.unrealize()

        if not os.path.isfile(CACHE_WALLPAPER_PATH):
            return

        self._windows = []

        for monitor_id in range(Utils.get_n_monitors()):
            gdkmonitor = Utils.get_monitor(monitor_id)
            if not gdkmonitor:
                return

            geometry = gdkmonitor.get_geometry()
            window = WallpaperLayerWindow(
                wallpaper_path=CACHE_WALLPAPER_PATH,
                gdkmonitor=gdkmonitor,
                width=geometry.width,
                height=geometry.height,
            )
            self._windows.append(window)
