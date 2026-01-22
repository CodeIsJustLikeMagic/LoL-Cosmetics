from pathlib import Path
import json
import cosmetics.dragon as cdragon
import cosmetics.util as util

ChampionSkinDict = dict[str, str| int| list]
"""dict of shape{"id": int, "name": str, "isBase": bool,
    "skinLines": [{"id": int}],
    "championId": int,
    "championName": str,
    "owned": bool,
    "chromas"(optional): list[ChampionSkinDict]
    "wards": { "skin_theme": list[SkinThemeDict]},
    "universes": list[str]
    "multiverse": list[str]}
"""

def get_champion_skin_keywords(c_skin):
    keyword:str = c_skin["name"]
    keyword = keyword.replace(c_skin["championName"], "")
    for sub_name in c_skin["championName"].split(" "):
        keyword = keyword.replace(sub_name, "")
    keyword = keyword.replace("Prestige", "")
    keyword = util.remove_date(keyword)
    keyword = keyword.replace("()", "")
    keyword = keyword.replace("( )", "")
    keyword = keyword.strip()
    return keyword

def get_champion_skins() -> dict[str: ChampionSkinDict]:
    """
    returns a dict of shape: { championId (int) : {skin_id (int): ChampionSkinDict }}
    """
    skinline_per_skin = cdragon.get_champion_skins()
    skinline_per_skin: dict[str, list] = {skin["id"]: skin["skinLines"]
                        for skin in skinline_per_skin.values()}
    # used to add "skinLines" key

    # filter out legacy skinline. It's to messy to be any good
    skinline_per_skin = {sk_id: sk_line for sk_id, sk_line in skinline_per_skin.items() if sk_line != [{"id": 167}]}

    with Path("data/lcu_cache/champions.json").open() as f:
        champions = json.load(f) # includes ownership per skin and chroma
        # list of champ dicts.
        # champ dict:
        #   {"id": int, name:"str", "skins":}
    print("hey")
    skins = {}
    for champ in champions:
        champ_skins = champ.get("skins", [])
        for skin in champ_skins:
            skin_id = skin["id"]
            skin_entry = {
                "id" : skin_id,
                "name" : skin["name"],
                "championId": skin["championId"],
                "championName": champ["name"],
                "isBase": skin["isBase"],
                "owned" : skin["ownership"]["owned"],
                "skinLines" : skinline_per_skin.get(skin_id, [])
            }
            if "chromas" in skin:
                chromas = []
                for chroma in skin["chromas"]:
                    chromas.append({
                        "id": chroma["id"],
                        "name": chroma["name"],
                        "isChroma": True,
                        "championId": chroma["championId"],
                        "championName": champ["name"],
                        "owned": chroma["ownership"]["owned"]
                    })
                skin_entry["chromas"] = chromas
            
            skins[skin_id] = skin_entry
        
    with open("data/debug/skins_debug_minimized.json", "w") as f:
        json.dump(skins, f, indent=2)
    return skins

def get_selectable_champion_skins(champ_skins: dict[str: ChampionSkinDict]):
    skins_per_champ = {}
    for skin in champ_skins.values():
        if skin["owned"] and not skin.get("isChroma", False) and not skin.get("isBase", False):
            champ_id = skin["championId"]
            util.ensure_exists(skins_per_champ, champ_id, [])
            entry = {"id": skin["id"],
                     "name": skin["name"],
                     "chromas": [{"id": c["id"], "name": c["name"]} for c in skin.get("chromas",[]) if c["owned"]]}
            skins_per_champ[champ_id].append(entry)
    return skins_per_champ
