import random
import enum
import cosmetics.ward_util as ward_util
import cosmetics.emote_util as emote_util
import cosmetics.skin_util as skin_util
from cosmetics.ward_util import CosmeticDict
from pathlib import Path
import json
import cosmetics.util as util


class SelectionMode(enum.Enum):
    RANDOM = 0
    SKIN_THEME = 1
    REGION = 2
    SEASON = 3

class SkinSelector:

    bann_list_path = "bann_list.json"

    selection_mode = SelectionMode.SKIN_THEME
    respect_banned = True

    def __init__(self):
        self._load_banned_list()
        print("\nSkinSelector - initializing")
        
        ## grab data ##
        all_champ_skins: dict[int: skin_util.ChampionSkinDict] = skin_util.get_champion_skins()
        self.champ_skins, self.all_ward_skins = ward_util.assign_ward_to_skins(all_champ_skins)
        self.champ_skins, self.all_ward_skins = ward_util.remove_not_owned(self.champ_skins, self.all_ward_skins)
        print("user owned wards: ", len(self.all_ward_skins))

        self.skins_per_champ = skin_util.get_selectable_champion_skins(self.champ_skins)
        self.all_emotes, self.emotes_per_champ = emote_util.get_emotes_per_champ_id()

        print("SkinSelector - ready!")
    
    def select_ward(self, champ_skin_id, champion_id, avoid: list[int] = [], skin_selection_mode: SelectionMode |None = None) -> CosmeticDict:
        if self.respect_banned:
            banned_ids = [ward["id"] for ward in self.bann_list["wards"]]
            avoid.extend(banned_ids)

        if skin_selection_mode is None:
            skin_selection_mode = self.selection_mode
        print(f"------ select ward ({skin_selection_mode})--------")
        match skin_selection_mode:
            case SelectionMode.RANDOM:
                return self.get_random_ward(avoid)
            case SelectionMode.SKIN_THEME:
                skin = self.get_themed_ward(champ_skin_id, avoid)
                if skin is None:
                    return self.select_ward(champ_skin_id, champion_id, avoid, SelectionMode.RANDOM) # Should be region
                else:
                    return skin
            case SelectionMode.REGION:
                skin = self.get_regional_ward(champion_id, avoid)
                if skin is None:
                    return self.select_ward(champ_skin_id, champion_id, avoid, SelectionMode.RANDOM)
                else:
                    return skin
            case SelectionMode.SEASON:
                skin = self.get_seasonal_ward(avoid)
                if skin is None:
                    return self.select_ward(champ_skin_id, champion_id, avoid, SelectionMode.SKIN_THEME)
                else:
                    return skin
        raise ValueError(f"Unexpected value {skin_selection_mode} for ward skin selection mode")

    def get_random_ward(self, avoid: list[int] = []) -> CosmeticDict:
        print("select random ward")
        return self._choose_from(self.all_ward_skins, avoid)
    
    def get_themed_ward(self, champ_skin_id:int, avoid: list[int] = []) -> CosmeticDict|None:
        skin = self.champ_skins[int(champ_skin_id)]
        print(f"select themed ward for {skin["name"]}, universe: {skin.get("universes")} mutliverse: {skin.get("multiverse")}")
        available_wards = skin.get("wards",{}).get("skin_theme",[])
        print(f"Avaliable: {len(available_wards)} - {[e["name"] for e in available_wards]}")
        selected = self._choose_from(available_wards, avoid)
        if selected is None:
            print("no themed wards available")
        return selected
    
    def get_regional_ward(self, champion_id, avoid: list[int] = []) -> CosmeticDict| None:
        print("select regional ward")
        print("no regional wards available")
        raise NotImplementedError()
    
    def get_seasonal_ward(self, avoid: list[int] = []) -> CosmeticDict|None:
        print("select seasonal ward")
        print("no seasonal wards available")
        raise NotImplementedError()
    
    def select_emote(self, champion_id, avoid: list[int] = []) -> CosmeticDict | None:
        print(f"Selecting emote for champion {champion_id}. Avoiding emote: {avoid}. ", end="")
        if self.respect_banned:
            banned_ids = [emote["id"] for emote in self.bann_list["emotes"]]
            avoid.extend(banned_ids)
        available_emotes = self.emotes_per_champ.get(champion_id, [])
        print(f"Available: {len(available_emotes)} - {[e["name"] for e in available_emotes]}")
        return self._choose_from(available_emotes, avoid)
    
    def select_random_skin(self, champion_id, avoid: list[int]= []) -> CosmeticDict | None:
        print(f"Selecting skin for champion {champion_id}. Avoiding skins: {avoid}. ", end="")
        if self.respect_banned:
            banned_ids = [skin["id"] for skin in self.bann_list.get("skins",[])]
            avoid.extend(banned_ids)
        available_skins = self.skins_per_champ.get(champion_id, [])
        print(f"Available: {len(available_skins)}")
        
        selected = self._choose_from(available_skins, avoid)
        if "chromas" in selected:
            selected = self._choose_from(selected["chromas"] + [selected])
        return selected

    @staticmethod
    def _choose_from(available_items: list[CosmeticDict], avoid: int|list[int] = []):
        if isinstance(avoid, int):
            avoid = [avoid]

        if len(available_items) == 0:
            return None
        print("choose first pick")
        prefered_items = [item for item in available_items if item["id"] not in avoid]
        if len(prefered_items) != 0:
            selected = random.choice(prefered_items)
        else:
            selected = random.choice(available_items)
        return selected

    def _load_banned_list(self):
        p = Path(self.bann_list_path)
        if p.exists():
            with p.open() as f:
                self.bann_list = json.load(f)
        else:
            self.bann_list = {"wards" : [],
                              "emotes" : [],
                              "skins": []}
    
    def _save_banned_list(self):
        with open(self.bann_list_path, "w") as f:
            json.dump(self.bann_list, f, indent=2)
    
    def bann_emote(self, emote_id:int):
        print("bann emote with id", emote_id)
        emote = [emote for emote in self.all_emotes if emote["id"] == emote_id]
        if len(emote) == 1:
            util.ensure_exists(self.bann_list, "emotes", [])
            self.bann_list["emotes"].append(emote[0])
            print("banned emote", emote)
        else:
            print("banning emote failed")
        self._save_banned_list()
    
    def bann_ward(self, ward_id:int):
        print("bann ward with id", ward_id)
        ward = [ward for ward in self.all_ward_skins if ward["id"] == ward_id]
        if len(ward) == 1:
            util.ensure_exists(self.bann_list, "wards", [])
            self.bann_list["wards"].append(ward[0])
            print("banned ward", ward)
        else:
            print("banning ward failed")
        self._save_banned_list
    
    def bann_skin(self, chamipon_id, skin_id:int):
        print("bann skin with id", skin_id)
        skins_of_champion = self.skins_per_champ.get(chamipon_id, [])
        skin = [skin for skin in skins_of_champion if skin["id"] == skin_id]
        if len(skin) == 1:
            util.ensure_exists(self.bann_list, "skins", [])
            self.bann_list["skins"].append(skin[0])
            print("banned skin", skin)
        else:
            print("banning skin failed")
        self._save_banned_list


if __name__ == "__main__":

    s = SkinSelector()

    print(s.select_emote(89))