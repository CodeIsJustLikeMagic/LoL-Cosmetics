import cosmetics.dragon as cdragon
from pathlib import Path
import json
import re
import cosmetics.selection.util as util
import cosmetics.selection.skin_util as skin_util
import cosmetics.logging_config as logging_config
from cosmetics.paths import DATA_PATHS
logger = logging_config.get_logger(__name__)

CosmeticDict = dict[str, int|str]
"""dict of shape:
    {"id": int, 
    "name": str}"""

def contains_word(keyword, text):
    """Returns true if the text contains the keyword."""
    # \b ensures the keyword is not part of another word
    # re.IGNORECASE is usually helpful for LoL data
    pattern = rf"\b{re.escape(keyword)}\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def get_skins_in_skinlines(skin_line_ids: list, champion_skins: list):
    skins = []
    for skin_set_id in skin_line_ids: 
        for c_skin in champion_skins:
            if c_skin["skinLines"] is not None:
                for champon_skin_line in c_skin["skinLines"]:
                    if champon_skin_line["id"] == skin_set_id:
                        skins.append(c_skin)
    return skins


def add_ward_keywords(ward_skins, ward_sets):
    # find keywords for wards
    for ward in ward_skins:
        keywords = []
        # we try to get a ward_set
        for ward_set in ward_sets.values():
            if ward["id"] in ward_set["wards"]:
                set_name = ward_set["displayName"]
                keywords.append(set_name)
        ward_name = ward["name"]
        keyword = ward_name
        keyword = keyword.replace("Ward", "")
        keyword = util.remove_date(keyword)
        keyword = keyword.strip()
        keywords.append(keyword)
        ward["keywords"] = keywords
    return ward_skins

def get_wards_matching_keywords(universe_keywords: list[str], ward_skins: dict, explicit_add_or_bann_list:list[str]):
    selected_ward_ids = []
    reasons_per_ward = {}
    for ward in ward_skins:
        ward_keywords = ward["keywords"]
        reasons = []
        selected = False
        banned = [name[1:] for name in explicit_add_or_bann_list if name.startswith("!")]
        requested = [name for name in explicit_add_or_bann_list if not name.startswith("!")]

        if ward["name"] in banned:
            # ward name explicitly banned
            selected = False
            continue
        elif ward["name"] in requested:
            # ward name explicitly requested
            selected = True
            reasons.append(f"ward name {ward['name']} explicitly requested")
        else:
            # check of keyword match in name or description.
            for u_kw in universe_keywords:
                if u_kw.startswith("!"):
                    continue
                for w_kw in ward_keywords:
                    if contains_word(u_kw, w_kw) or contains_word(w_kw, u_kw):
                        selected = True
                        reasons.append(f"keyword match: {u_kw} - {w_kw}")
                descs = [rd["description"] for rd in ward["regionalDescriptions"]]
                for desc in descs:
                    if contains_word(u_kw, desc):
                        selected = True
                        reasons.append(f"description match: {u_kw}")
        if selected:
            selected_ward_ids.append(ward["id"])
        reasons_per_ward[ward["id"]] = reasons

    all_ward_skins_by_id = {w["id"]: w for w in ward_skins}
    return [{"id": ward_id, 
             "name": all_ward_skins_by_id[ward_id]["name"], 
             "reasons": reasons_per_ward[ward_id]} for ward_id in set(selected_ward_ids)]

def apply_keyword_tweak(keywords: list[str], tweak_keywords: list[str]):
    """
    Adds keywords from the tweak list to the keywords list.
    Removes keywords instead, if they start with ! . e.g: !Worlds
    """
    for t_kw in tweak_keywords:
        if t_kw.startswith("!"):
            # e.g: tweak: "!Spirit Blossom" -> should remove "Spirit Blossom After Hours" keyword.
            now_allowed = t_kw[1:]
            keywords = [kw for kw in keywords if not contains_word(now_allowed, kw)]
        else:
            # nomral add keyword.
            if t_kw not in keywords:
                keywords.append(t_kw)
    return keywords

WardSkinsDict = dict[str, any]
"""dict of shape {
    "id": int, "name":str, "description": str | "",
    "wardImagePath": str, "wardShadowImagePath": str,
    "contentId": str, "isLegacy": bool,
    "regionalDescriptions": [{"region": "riot", "description": str}],
    "rarities": [{"region": "riot", "rarity": int}]
    "keywords": list[str]
  },
"""

def assign_ward_to_skins(all_champ_skins: dict[str: any], tweaks: dict) -> tuple[dict[str: skin_util.ChampionSkinDict],  list[WardSkinsDict]]:
    """
    Adds a list of wards skins to each champion skin.
    Wards are added based on skin_theme (keyword matching, skinline, universe and multiverse sets)

    Returns: all_champ_skins dict[str(skin_id): ChampionSkinsDict], all_ward_skins
    ready in lcu_cache/skins-minimal.json, and pulls data from cdragon about skins, universes and wards.
    """
    
    all_universes = cdragon.get_universes()

    all_ward_sets = cdragon.get_ward_sets()
    all_ward_sets = {s["id"]: s for s in all_ward_sets}

    all_skinlines = cdragon.get_skinlines()
    all_skinlines = {s["id"]: s for s in all_skinlines}

    all_ward_skins: list[WardSkinsDict] = cdragon.get_ward_skins()
    all_ward_skins = add_ward_keywords(all_ward_skins, all_ward_sets)

    skin_lines_in_universe = [u["skinSets"] for u in all_universes]
    skin_lines_in_universe = [id for idlist in skin_lines_in_universe for id in idlist]
    max_id = max([u["id"] for u in all_universes])
    new_universes = []
    for skin_line in all_skinlines.values():
        if skin_line["id"] not in skin_lines_in_universe:
            max_id += 1
            new_universe_entry = {
                "id" : max_id,
                "name" : f"generated - {skin_line["name"]}",
                "skinSets" : [skin_line["id"]],
            }
            new_universes.append(new_universe_entry)
    all_universes.extend(new_universes)

    ## match wards to skin-themes ##

    # add keywords to skinSets in each universe.
    # turn the skinSets list[int] in universes.json into dict like: {"id": int, "name": str, "keywords": list[str]}
    for universe in all_universes:
        c_skin_Sets = universe["skinSets"]
        universe["skinSets"] = []
        for skin_set_id in c_skin_Sets: 
            skin_line = all_skinlines[skin_set_id]
            keywords = [skin_line["name"], universe["name"]]

            skins_in_skinline = get_skins_in_skinlines([skin_set_id], all_champ_skins.values())
            for c_skin in skins_in_skinline:
                keyword = skin_util.get_champion_skin_keywords(c_skin)
                if keyword != "":
                    keywords.append(f"{keyword}")
            skin_line["skin_keywords"] = list(set(keywords))
            skin_line["skin_ids"] = [s["id"] for s in skins_in_skinline]
            universe["skinSets"].append(skin_line)

    # compile the keywords of each mutliverse from tweaks list and from universes and their skinlines
    # select wards for the universe.
    used_wards = []
    in_multiverse = []
    for multiverse in tweaks["multiverses"]:
        # universes in this multiverse. 
        m_universes = [universe for universe in all_universes if universe["name"] in multiverse["universes"]]
        in_multiverse.extend(multiverse["universes"])
        
        m_verse_keywords = [] # we start with mutliverse
        for universe in m_universes:
            for skin_set in universe["skinSets"]:
                kdws = skin_set.get("skin_keywords")
                if kdws is not None:
                    m_verse_keywords.extend(kdws)
        m_verse_keywords = apply_keyword_tweak(m_verse_keywords, tweaks["omniverse-keywords"])
        m_verse_keywords = apply_keyword_tweak(m_verse_keywords, multiverse.get("keywords",[]))
        # logger.info(f"mutliverse: {mutliverse["name"]} - {[u["name"] for u in m_universes]}")
        # logger.info(f"    {m_verse_keywords}")

        # mutliverse  "wards" - list to add or bann a ward from multiverse list.
        explicit_bann_or_add_list = multiverse.get("wards",[])
        selected_wards = get_wards_matching_keywords(m_verse_keywords, all_ward_skins, explicit_bann_or_add_list)

        used_wards.extend([s["id"] for s in selected_wards])
        multiverse["ward_cnt"] = len(selected_wards)
        multiverse["wards"] = [w["name"] for w in selected_wards]
        for universe in m_universes:
            universe["ward_cnt"] = multiverse["ward_cnt"]
            universe["wards"] = selected_wards
        
    other_universes = [universe for universe in all_universes if universe["name"] not in in_multiverse]
    #logger.info("other_universes", [o["name"] for o in other_universes])

    for universe in other_universes:
        u_verse_keywords = []
        for skin_set in universe["skinSets"]:
                kdws = skin_set.get("skin_keywords")
                if kdws is not None:
                    u_verse_keywords.extend(kdws)
        selected_wards = get_wards_matching_keywords(u_verse_keywords, all_ward_skins, [])
        used_wards.extend([s["id"] for s in selected_wards])
        selected_wards = [w["name"] for w in selected_wards]
        tweaks["multiverses"].append({"name": f"generated - {universe["name"]}", 
                                        "universes": [universe["name"]],
                                        "ward_cnt": len(selected_wards),
                                        "wards": selected_wards})

    # now, we've added a "wards" list to all multiverses (and to the universes in "other")
    # add wards to skins.

    for multiverse in tweaks["multiverses"]:
        # universes in this multiverse. 
        m_wards = multiverse.get("wards", [])
        m_wards = [{"id": w["id"], "name": w["name"]} for w in all_ward_skins if w["name"] in m_wards]
        m_universes = [universe for universe in all_universes if universe["name"] in multiverse["universes"]]
        for universe in m_universes:
            u_skin_ids = [sset["skin_ids"] for sset in universe["skinSets"]]
            u_skin_ids = [x for xs in u_skin_ids for x in xs]
            for s_id in u_skin_ids:
                skin = all_champ_skins[s_id]
                if "wards" not in skin:
                    skin["wards"] = {}
                skin["wards"]["skin_theme"] = skin["wards"].get("skin_theme", [])
                skin["wards"]["skin_theme"].extend(m_wards)

                skin["universes"] = skin.get("universes", [])
                if universe["name"] not in skin["universes"]:
                    skin["universes"].append(universe["name"])

                skin["multiverse"] = skin.get("multiverse", [])
                if multiverse["name"] not in skin["multiverse"]:
                    skin["multiverse"].append(multiverse["name"])
    
    chromas = {}
    for skin in all_champ_skins.values():
        for chroma in skin.get("chromas"):
            chroma_entry = {"id": chroma["id"],
                            "name": chroma["name"],
                            "isChroma": True,
                            "owned" : skin["owned"],
                            "championId": skin["championId"],
                            "championName": skin["championName"]}
            if "wards" in skin:
                ward_addition = {"wards": skin.get("wards", {}),
                                "universes": skin["universes"],
                                "multiverse": skin["multiverse"]}
                chroma_entry.update(ward_addition)
            
            chromas[chroma["id"]] = chroma_entry
    all_champ_skins.update(chromas)
            

    ## debug ##
    with (DATA_PATHS.debug_cache / "skins_debug.json").open("w") as f:
        json.dump(all_champ_skins, f, indent=2)

    with (DATA_PATHS.debug_cache / "mutliverse_debug.json").open("w") as f:
        json.dump(tweaks, f, indent=2)

    all_ward_skins_by_id = {s["id"]: s for s in all_ward_skins}
    not_used = [ward_id for ward_id in all_ward_skins_by_id.keys() if ward_id not in used_wards and ward_id != 0]
    if len(not_used) == 0:
        logger.info("all wards assigned!")
    else:
        logger.info("--- unassigned wards ----")
        for w in not_used:
            logger.info(f"    w - {all_ward_skins_by_id[w]['name']}")

    with (DATA_PATHS.debug_cache/ "universes_merged.json").open("w") as f:
        json.dump(all_universes, f, indent=2)
    

    return all_champ_skins, all_ward_skins

def remove_not_owned(champ_skins: dict[str, skin_util.ChampionSkinDict], all_ward_skins: list[WardSkinsDict]) -> tuple[dict[str, skin_util.ChampionSkinDict],  list[WardSkinsDict]]:
    # remove unowned skins
    with Path(DATA_PATHS.lcu_cache / "ward_skin_collection.json").open() as f:
        ward_ownership = json.load(f)
    owned_ward_ids = [w["id"] for w in ward_ownership if w["ownership"]["owned"] or w["id"] == 0]
    all_ward_skins = [w for w in all_ward_skins if w["id"] in owned_ward_ids]

    for skin in champ_skins.values():
        if "wards" in skin:
            if "skin_theme" in skin["wards"]:
                available = [w for w in skin["wards"]["skin_theme"] if w["id"] in owned_ward_ids]
                skin["wards"]["skin_theme"] = available

    return champ_skins, all_ward_skins
