import pytest
from cosmetics.skin_selector import SkinSelector
from pathlib import Path

@pytest.fixture(scope="module", autouse=True)
def skinselector():
    yield SkinSelector()

def test_consictenty(skinselector: SkinSelector):
    skins = skinselector.champ_skins
    assert all([isinstance(k, int) for k in skins.keys()]), "all champ skins should have int as key"

def test_removed_unavailable_wars(skinselector: SkinSelector):
    skins = skinselector.champ_skins
    assert "Crystalis Motus Ward" not in [w["name"] for w in skins[28024]["wards"]["skin_theme"]]

def test_selection_1(skinselector: SkinSelector):
    skin = skinselector.get_themed_ward(111018)
    assert skin is not None

def test_selection_chroma_2(skinselector:SkinSelector):
    skin = skinselector.select_ward(111033, 0)
    assert skin["name"] in [
        "Astronaut Poro Ward",
        "Galaxies 2020 Ward",
        "Exo-Ward",
        "Starcall Ward",
        "Space & Time Ward",
        "Corruptant Ward",
        "Space Lizard Ward",
        "2021 Space Groove Ward",
        "Gold Space Lizard Ward",
        "Dark Star Ward",
        "Glorious Legend Ward"
      ]

def test_generate_universe(skinselector:SkinSelector):
    skins = skinselector.champ_skins
    assert skins[902011].get("universes") is not None

def test_banned_emote(skinselector:SkinSelector):
    emotes = [skinselector.select_emote(89, avoid=[3170]) for i in range(10)]
    assert 3170 not in [emote["id"] for emote in emotes]

def test_banned_emote_2(skinselector:SkinSelector):
    emotes = [skinselector.select_emote(267, avoid=[4037]) for i in range(10)]
    assert 4037 not in [emote["id"] for emote in emotes]

def test_choose_skin_with_chroma(skinselector:SkinSelector):
    skins = [skinselector.select_random_skin(25)]
    print(skins)

def test_base_skin_shoulnt_be_in_universe(skinselector:SkinSelector):
    for skin in skinselector.champ_skins.values():
        if skin.get("isBase", False):
            if "Doom Bot" not in skin.get("name"):
                assert skin.get("multiverse") is None

def test_removed_legacy_skinlines(skinselector:SkinSelector):
    leona_legacy = skinselector.champ_skins[89002]
    assert leona_legacy.get("multiverse") is None