import requests
import json
from pathlib import Path
import cosmetics.logging_config as logging_config
from cosmetics.paths import DATA_PATHS
logger = logging_config.get_logger("cDragon")

source_path = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1"

def get_champion_skins(force_refresh: bool = False):
    return get_cdragon("skins.json", f"{source_path}/skins.json", force_refresh=force_refresh)

def get_universes(force_refresh: bool = False):
    return get_cdragon("universes.json", f"{source_path}/universes.json", force_refresh=force_refresh)

def get_ward_sets(force_refresh: bool = False):
    return get_cdragon("ward_skin_sets.json", f"{source_path}/ward-skin-sets.json", force_refresh=force_refresh)

def get_skinlines(force_refresh: bool = False):
    return get_cdragon("skinlines.json", f"{source_path}/skinlines.json", force_refresh=force_refresh)

def get_ward_skins(force_refresh: bool = False):
    return get_cdragon("ward_skins.json", f"{source_path}/ward-skins.json", force_refresh=force_refresh)

def get_champion_summary(force_refresh: bool = False):
    return get_cdragon("champion_summary.json", f"{source_path}/champion-summary.json", force_refresh=force_refresh)

def get_summoner_emotes(force_refresh: bool = False):
    return get_cdragon("summer_emotes.json", f"{source_path}/summoner-emotes.json", force_refresh=force_refresh)

def get_cdragon(file_name:str, url: str, force_refresh: bool = False) -> dict:
    out_path = DATA_PATHS.cdragon_cache / file_name
    if Path(out_path).exists() and not force_refresh:
        logger.info(f"{out_path} already exists, skipping download")
        with open(out_path, "r") as f:
            return json.load(f)
    try:
        r = requests.get(url, verify=False, timeout=30)
        r.raise_for_status()
        j = r.json()
    except (requests.exceptions.RequestException, ValueError):
        logger.exception(f"Error fetching {url}.")
        # Fall back to stale cache if we have one
        if out_path.exists():
            logger.warning(f"Using stale cache for {file_name}")
            with open(out_path, "r") as f:
                return json.load(f)
        else:
            logger.error(f"Request failed an no cache found for {file_name}.")
        return {}

    out_path.parent.mkdir(exist_ok=True, parents=True)
    tmp = out_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(j, f, indent=2)
    tmp.replace(out_path)
    # atomic swap, no half-written files

    logger.info(f"'.../{url.split("/")[-1]}' -> {out_path}")
    return j

def refresh_cache():
    # if cdragon is down, this failes gracefully. Warning of stale cache but not deleting outright.
    logger.info("refreshing cache")

    for fn in (get_champion_skins, get_universes, get_ward_sets, get_skinlines, get_ward_skins, get_champion_summary, get_summoner_emotes):
        fn(force_refresh=True)