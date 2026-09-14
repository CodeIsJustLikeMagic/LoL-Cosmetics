from pathlib import Path
import json
import cosmetics.selection.util as util
from cosmetics.selection.ward_util import CosmeticDict
from cosmetics.paths import DATA_PATHS

import cosmetics.logging_config as logging_config
logger = logging_config.get_logger(__name__)

class Config:
    def __init__(self, config_dir: Path | None = None):
        if config_dir is not None:
            config_dir = Path(config_dir)
        else:
            config_dir = DATA_PATHS.config_dir
        self.multiverses_path = config_dir/"multiverses.json"
        self.preferences_path = config_dir/"preferences.json"
        self.preferences = self._load_config(self.preferences_path, 
                                    {"banned" : {"wards" : [],
                                                "emotes" : [],
                                                "skins": []},
                                    "favourites": {"wards" : [],
                                                "emotes" : [],
                                                "skins": []}})
        self._save_config()

    def get_multiverses(self):
        with Path(self.multiverses_path).open() as f:
            tweaks = json.load(f)
        return tweaks
    
    ## -- direct accessors --
    def bann_cosmetic(self, cosmetic_id:int, categorie:str, data: list[dict]):
        """categorie: ["wards", "skins", "emotes"]"""
        self.add_cosmetic(cosmetic_id, f"banned/{categorie}", data)

    def favourite_cosmetic(self, cosmetic_id:int, categorie:str, data:list[dict]):
        """categorie: ["wards", "skins", "emotes"]"""
        self.add_cosmetic(cosmetic_id, f"favourites/{categorie}", data)

    def get_banned(self, categorie) -> list[int]:
        """categorie: ["wards", "skins", "emotes"]"""
        banned = self.preferences["banned"]
        return [item["id"] for item in banned[categorie]]
    
    def get_favourites(self, categorie) -> list[CosmeticDict]:
        """categorie: ["wards", "skins", "emotes"]"""
        favourites = self.preferences["favourites"]
        return favourites[categorie]
    
    # -- general --
    def add_cosmetic(self, cosmetic_id: int, config_path:str, data: list[dict]):
        cosmetic_dict = [item for item in data if item["id"] == cosmetic_id]

        config_path = config_path.split("/")
        if len(config_path) != 2:
            raise ValueError(f"config_path is expected to have shape <action>/<categorie>. Value passed: {config_path}")
        action, categorie = config_path

        action_list = self.preferences[action]
        if len(cosmetic_dict) == 1:
            cosmetic_dict = cosmetic_dict[0]
            cosmetic_dict = {"id" : cosmetic_dict["id"], "name": cosmetic_dict["name"]}# minimize dict

            util.ensure_exists(action_list, categorie, [])
            exisitng = [item["id"] for item in action_list[categorie]]
            if cosmetic_id in exisitng:
                logger.info(f"cosmetic {cosmetic_id} already in config {config_path}")
                return
            action_list[categorie].append(cosmetic_dict)
            logger.info(f"added cosmetic to {action}/{categorie} {cosmetic_dict}")
        else:
            logger.info(f"adding cosmetic to {action}/{categorie} failed")
        self._save_config()
        
    def _save_config(self):
        with open(self.preferences_path, "w") as f:
            json.dump(self.preferences, f, indent=2)

    @staticmethod
    def _load_config(path, default):
        p = Path(path)
        if p.exists():
            with p.open() as f:
                config = json.load(f)
        else:
            config = default
        return config
    
