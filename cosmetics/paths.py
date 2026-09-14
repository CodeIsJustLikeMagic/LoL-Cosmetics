from pathlib import Path
import shutil

import sys
class DataPaths:
    log_folder = Path()

    cache_folder_ = Path("cache")
    @property
    def cache_folder(self) -> Path:
        self.cache_folder_.mkdir(exist_ok=True)
        return self.cache_folder_

    @property
    def cdragon_cache(self) -> Path:
        p = self.cache_folder/"cdragon_cache"
        p.mkdir(exist_ok=True)
        return p

    @property
    def lcu_cache(self) -> Path:
        p = self.cache_folder / "lcu_cache"
        p.mkdir(exist_ok=True)
        return p

    @property
    def debug_cache(self) -> Path:
        p = self.cache_folder / "debug"
        p.mkdir(exist_ok=True)
        return p

    @property
    def _mei_pass(self) -> Path:
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        else:
            return Path()

    _config_path = Path("config")
    @property
    def config_dir(self) -> Path:
        if not self._config_path.exists():
            meipass = self._mei_pass / self._config_path
            if meipass.exists():
                self.copy_folder_to(meipass, self._config_path)
                # copy content of meipass to config_path
        
        self._config_path.mkdir(exist_ok=True)
        return self._config_path

    def allow_mei_pass(self, folder:Path) -> Path | None:
        locations = [folder, self._mei_pass / folder]
        for l in locations:
            if l.exists():
                return l
        return None

    _assets_path = Path("assets")
    @property
    def assets_path(self) -> Path:
        l = self.allow_mei_pass(self._assets_path)
        if l:
            return l
        msg = f"Folder {self._assets_path} was not found" 
        raise FileNotFoundError(msg)

    @staticmethod
    def clear(folder:Path):
        folder = Path(folder)
        if folder.exists():
            for f in folder.iterdir():
                if f.is_file():
                    f.unlink()

    @staticmethod
    def copy_folder_to(src_folder:Path, target_folder:Path):
        for src_file in src_folder.rglob("*"):
            if src_file.is_file():
                # Preserve subfolder structures inside config/
                relative_path = src_file.relative_to(src_folder)
                target_file = target_folder / relative_path

                # Restore missing or deleted user config files
                if not target_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, target_file)


DATA_PATHS = DataPaths()