import requests
import json
from pathlib import Path

cache_folder: Path = Path("data/cdragon_cache")

def get_champion_skins():
    return get_cdragon("skins.json", "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/skins.json")

def get_universes():
    return get_cdragon("universes.json", "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/universes.json")

def get_ward_sets():
    return get_cdragon("ward_skin_sets.json", "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/ward-skin-sets.json")

def get_skinlines():
    return get_cdragon("skinlines.json", "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/skinlines.json")

def get_ward_skins():
    return get_cdragon("ward_skins.json", "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/ward-skins.json")

def get_champion_summary():
    return get_cdragon("champion_summary.json", "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json")

def get_summoner_emotes():
    return get_cdragon("summer_emotes.json", "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/summoner-emotes.json")

def get_cdragon(file_name:str, url: str) -> dict:
    out_path = cache_folder / file_name
    if Path(out_path).exists():
        print(f"{out_path} already exists, skipping download")
        with open(out_path, "r") as f:
            return json.load(f)
    try:
        r = requests.get(url, verify=False)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {out_path} data: ", e)
        return {}
    j = json.loads(r.content)

    out_path.parent.mkdir(exist_ok=True, parents=True)
    with open(out_path, "w") as f:
        json.dump(j, f, indent=2)

    print("Fetched", len(j), f"{out_path} from CommunityDragon")
    return j
