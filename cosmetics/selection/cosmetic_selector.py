import random
import enum
import cosmetics.selection.ward_util as ward_util
import cosmetics.selection.emote_util as emote_util
import cosmetics.selection.skin_util as skin_util
from cosmetics.selection.ward_util import CosmeticDict
from cosmetics.selection.config import Config
from pathlib import Path

import cosmetics.logging_config as logging_config
logger = logging_config.get_logger(__name__)

class SelectionMode(enum.Enum):
    RANDOM = 0
    SKIN_THEME = 1
    REGION = 2
    SEASON = 3
    CHAMPION = 4
    FAVOURITES = 5

skin_id = str
class SkinSelector:
    selection_mode = SelectionMode.SKIN_THEME

    debug_path = Path("cache/debug")

    def __init__(self, config_dir: Path|None = None):
        self.config = Config(config_dir)
        multiverses = self.config.get_multiverses()
        logger.info("SkinSelector - initializing")
        
        ## grab data ##
        all_champ_skins: dict[skin_id, skin_util.ChampionSkinDict] = skin_util.get_champion_skins()
        self.champ_skins, self.all_ward_skins = ward_util.assign_ward_to_skins(all_champ_skins, multiverses, self.debug_path)
        self.champ_skins, self.all_ward_skins = ward_util.remove_not_owned(self.champ_skins, self.all_ward_skins)
        logger.info(f"user owned wards: {len(self.all_ward_skins)}")

        self.skins_per_champ = skin_util.get_selectable_champion_skins(self.champ_skins)
        self.all_emotes, self.emotes_per_champ = emote_util.get_emotes_per_champ_id(self.debug_path)

        logger.info(f"user owned emotes: {len(self.all_emotes)}")

        logger.info("SkinSelector - ready!")
    
    def select_ward(self, champ_skin_id, champion_id, avoid: list[int] = [], skin_selection_mode: SelectionMode |None = None) -> CosmeticDict:
        banned = self.config.get_banned("wards")

        if skin_selection_mode is None:
            skin_selection_mode = self.selection_mode
        logger.info(f"------ select ward ({skin_selection_mode})--------")
        match skin_selection_mode:
            case SelectionMode.RANDOM:
                return self._get_random_ward(avoid, banned)
            case SelectionMode.SKIN_THEME:
                skin = self._get_themed_ward(champ_skin_id, avoid, banned)
                if skin is None:
                    return self.select_ward(champ_skin_id, champion_id, avoid, SelectionMode.RANDOM) # Should be region
                else:
                    return skin
            case SelectionMode.REGION:
                skin = self._get_regional_ward(champion_id, avoid, banned)
                if skin is None:
                    return self.select_ward(champ_skin_id, champion_id, avoid, SelectionMode.RANDOM)
                else:
                    return skin
            case SelectionMode.SEASON:
                skin = self._get_seasonal_ward(avoid, banned)
                if skin is None:
                    return self.select_ward(champ_skin_id, champion_id, avoid, SelectionMode.SKIN_THEME)
                else:
                    return skin
        raise ValueError(f"Unexpected value {skin_selection_mode} for ward skin selection mode")

    def _get_random_ward(self, avoid: list[int] = [], banned: list[int] = []) -> CosmeticDict:
        logger.info("select random ward")
        return self._choose_from(self.all_ward_skins, avoid, banned)
    
    def _get_themed_ward(self, champ_skin_id:int, avoid: list[int] = [],  banned: list[int] = []) -> CosmeticDict|None:
        skin = self.champ_skins[int(champ_skin_id)]
        logger.info(f"select themed ward for {skin["name"]}, universe: {skin.get("universes")} mutliverse: {skin.get("multiverse")}")
        available_wards = skin.get("wards",{}).get("skin_theme",[])
        logger.info(f"Avaliable: {len(available_wards)} - {[e["name"] for e in available_wards]}")
        selected = self._choose_from(available_wards, avoid, banned)
        if selected is None:
            logger.info("no themed wards available")
        return selected
    
    def _get_regional_ward(self, champion_id, avoid: list[int] = [], banned: list[int] = []) -> CosmeticDict| None:
        logger.info("select regional ward")
        logger.info("no regional wards available")
        raise NotImplementedError()
    
    def _get_seasonal_ward(self, avoid: list[int] = [], banned: list[int] = []) -> CosmeticDict|None:
        logger.info("select seasonal ward")
        logger.info("no seasonal wards available")
        raise NotImplementedError()
    
    def select_emote(self, champion_id, avoid: list[int] = [], selection_mode: SelectionMode = SelectionMode.CHAMPION) -> CosmeticDict | None:
        logger.info("select emote")
        banned = self.config.get_banned("emotes")
        if champion_id == -1:
            selection_mode = SelectionMode.FAVOURITES

        match selection_mode:
            case SelectionMode.CHAMPION:
                emote = self._get_champion_emote(champion_id, avoid, banned)
                if emote is None:
                    return self.select_emote(champion_id, avoid, SelectionMode.FAVOURITES)
                else:
                    return emote
            case SelectionMode.FAVOURITES:
                return self._get_favourite_emote(avoid, banned)
        raise ValueError(f"Unexpected value {selection_mode} for emote selection mode") 
                
        
    def _get_favourite_emote(self, avoid: list[int] = [], banned: list[int] = []):
        favourites = self.config.get_favourites("emotes")
        owned_ids = [e["id"] for e in self.all_emotes]
        available_emotes = [e for e in favourites if e["id"] in owned_ids]
        logger.info(f"Available favourite emotes: {len(available_emotes)} - {[e["name"] for e in available_emotes]}")
        return self._choose_from(available_emotes, avoid, banned)
    
    def _get_champion_emote(self, champion_id, avoid: list[int] = [], banned: list[int] = []):
        logger.info(f"Selecting emote for champion {champion_id}. Avoiding emote: {avoid}. Banned {banned} ", end="")
        available_emotes = self.emotes_per_champ.get(champion_id, [])
        logger.info(f"Available: {len(available_emotes)} - {[e["name"] for e in available_emotes]}")
        return self._choose_from(available_emotes, avoid, banned)

    def bann_emote(self, emote_id:int):
        logger.info("bann emote with id", emote_id)
        self.config.bann_cosmetic(emote_id, "emotes", self.all_emotes)
    
    def bann_ward(self, ward_id:int):
        logger.info("bann ward with id", ward_id)
        self.config.bann_cosmetic(ward_id, self.all_ward_skins, "wards")
    
    def bann_skin(self, chamipon_id, skin_id:int):
        logger.info("bann skin with id", skin_id)
        skins_of_champion = self.skins_per_champ.get(chamipon_id, [])
        self.config.bann_cosmetic(skin_id, skins_of_champion, "skins")

    def favourite_emote(self, ward_id:int):
        logger.info("favourite emote with id ", ward_id)
        self.config.favourite_cosmetic(ward_id, "emotes", self.all_emotes)
    
    def select_random_skin(self, champion_id, avoid: list[int]= []) -> CosmeticDict | None:
        logger.info(f"Selecting skin for champion {champion_id}. Avoiding skins: {avoid}. ", end="")
        
        available_skins = self.skins_per_champ.get(champion_id, [])
        logger.info(f"Available: {len(available_skins)}")
        banned = self.config.get_banned("skins")
        selected = self._choose_from(available_skins, avoid, banned)
        if "chromas" in selected:
            selected = self._choose_from(selected["chromas"] + [selected], avoid, banned)
        return selected

    @staticmethod
    def _choose_from(available_items: list[CosmeticDict], avoid: int|list[int] = [], banned: list[int] = []):
        if isinstance(avoid, int):
            avoid = [avoid]

        available_items = [item for item in available_items if item["id"] not in banned]
        prefered_items = [item for item in available_items if item["id"] not in avoid]

        if len(available_items) == 0:
            return None
        if len(prefered_items) != 0:
            selected = random.choice(prefered_items)
        else:
            selected = random.choice(available_items)
        return selected

if __name__ == "__main__":

    s = SkinSelector()

    logger.info(s.select_emote(89))