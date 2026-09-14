import pytest
from cosmetics.selection.cosmetic_selector import CosmeticSelector
from pathlib import Path

@pytest.fixture(scope="module", autouse=True)
def skinselector():
    yield CosmeticSelector()

def test_consictenty(skinselector: CosmeticSelector):
    skins = skinselector.champ_skins
    assert all([isinstance(k, int) for k in skins.keys()]), "all champ skins should have int as key"

def test_removed_unavailable_wars(skinselector: CosmeticSelector):
    skins = skinselector.champ_skins
    assert "Crystalis Motus Ward" not in [w["name"] for w in skins[28024]["wards"]["skin_theme"]]

def test_selection_1(skinselector: CosmeticSelector):
    skin = skinselector._get_themed_ward(111018)
    assert skin is not None

def test_selection_chroma_2(skinselector:CosmeticSelector):
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

def test_generate_universe(skinselector:CosmeticSelector):
    skins = skinselector.champ_skins
    assert skins[902011].get("universes") is not None

def test_banned_emote(skinselector:CosmeticSelector):
    emotes = [skinselector.select_emote(89, avoid=[3170]) for i in range(10)]
    assert 3170 not in [emote["id"] for emote in emotes]

def test_banned_emote_2(skinselector:CosmeticSelector):
    emotes = [skinselector.select_emote(267, avoid=[4037]) for i in range(10)]
    assert 4037 not in [emote["id"] for emote in emotes]

def test_choose_skin_with_chroma(skinselector:CosmeticSelector):
    skins = [skinselector.select_random_skin(25)]

def test_base_skin_shoulnt_be_in_universe(skinselector:CosmeticSelector):
    for skin in skinselector.champ_skins.values():
        if skin.get("isBase", False):
            if "Doom Bot" not in skin.get("name"):
                assert skin.get("multiverse") is None

def test_removed_legacy_skinlines(skinselector:CosmeticSelector):
    leona_legacy = skinselector.champ_skins[89002]
    assert leona_legacy.get("multiverse") is None

def test_mythmaker_zyra(skinselector:CosmeticSelector):
    mythmaker_zyra = skinselector.champ_skins[143036]
    themed_wards = mythmaker_zyra["wards"]["skin_theme"]
    wards = [w["name"] for w in themed_wards]
    assert "Gong Ward" in wards
    # mythmaker zyra should be in lunar revel universe

def test_pool_part_leona(skinselector:CosmeticSelector):
    ppleona = skinselector.champ_skins[89004]
    themed_wards = ppleona["wards"]["skin_theme"]
    wards = [w["name"] for w in themed_wards]
    assert "2025 Spirit Blossom Ward" not in wards

def test_zyra_emote(skinselector:CosmeticSelector):
    emote = skinselector.select_emote(143) # zyra
    assert emote is not None
    assert emote["id"] in [item["id"] for item in skinselector.config.get_favourites("emotes")]
    # when selecting zyra all emotes of her are banned. This should fallback on a favourites list

def test_nautilus_selectable_skins(skinselector:CosmeticSelector):
    nautilus = 111
    all_skins = skinselector.champ_skins
    naut_skins = [skin for skin in all_skins.values() if skin["championId"] == nautilus]
    assert len(naut_skins) > 0, "There are some nautilus skins in general"
    assert any(skin.get("isChroma", False) for skin in naut_skins), "Nautilus should have some chromas"
    assert any(not skin.get("isChroma", False) for skin in naut_skins), "Nautilus should have some none-chroma skins"