from pathlib import Path
import json
import cosmetics.dragon as dragon
import cosmetics.util as util
from cosmetics.ward_util import CosmeticDict

EmotesPerChampIdDict = dict[str:list[CosmeticDict]]
"""
dict of shape:
{champion_id (str): list[CosmeticDict]]}
"""
def get_emotes_per_champ_id(remove_not_owned = True) -> tuple[dict, EmotesPerChampIdDict]:
    all_emotes = dragon.get_summoner_emotes()

    if remove_not_owned:
        with Path("data/lcu_cache/emotes.json").open() as f:
            emote_ownership = json.load(f)
        
        emote_ownership = {e["itemId"]: e["owned"] for e in emote_ownership}
        all_emotes = [emote for emote in all_emotes if emote_ownership.get(emote["id"], False) == True]
    emotes_per_champ_id:EmotesPerChampIdDict = {}
    for emote in all_emotes:
        champ_ids = emote["taggedChampionsIds"]
        for champ_id in champ_ids:
            util.ensure_exists(emotes_per_champ_id, champ_id, [])
            emotes_per_champ_id[champ_id].append({"id": emote["id"], "name": emote["name"], "inventoryIcon": emote["inventoryIcon"]})
    with open("data/debug/emotes_per_champ_id.json", "w") as f:
        json.dump(emotes_per_champ_id, f, indent=2)

    return all_emotes, emotes_per_champ_id
        