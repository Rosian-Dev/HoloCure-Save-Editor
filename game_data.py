"""Static game knowledge: master ID lists, display names and field labels.

These lists target HoloCure ~v0.7. They are intentionally treated as a *floor*:
the editor unions them with whatever IDs are actually present in a loaded save
(see ``editor model``), so newer/unknown content is never hidden or dropped.

Achievements and the character roster are NOT hard-coded here because a save
already contains the complete set for its own version; the editor derives those
from the loaded file.
"""

from __future__ import annotations

import re

# --- Currency (top-level numeric fields) -------------------------------------
CURRENCY_FIELDS: dict[str, str] = {
    "holoCoins": "Holo Coins",
    "fishSand": "Fish Sand",
    "holoChips": "Holo Chips (Casino)",
    "usadaDrinks": "Usada Drinks",
}

# --- Permanent upgrade levels (Holo House shop), top-level numeric fields -----
STAT_FIELDS: dict[str, str] = {
    "ATK": "Attack",
    "HP": "Max HP",
    "SPD": "Move Speed",
    "crit": "Crit",
    "haste": "Haste",
    "regen": "HP Regen",
    "DR": "Damage Reduction",
    "growth": "Growth (EXP)",
    "moneyGain": "Money Gain",
    "pickupRange": "Pickup Range",
    "eliminate": "Eliminate",
    "skillDamage": "Skill Damage",
    "food": "Food",
    "supports": "Supports",
    "reroll": "Reroll",
    "enhanceUp": "Enhance",
    "specCDR": "Special CDR",
    "holdOption": "Hold Option",
}

# --- Playable characters (id -> display name) --------------------------------
# Stored in the save's `characters` / `fandomEXP` / `characterClears` arrays.
# Meta entries (random / none / empty) are skipped here on purpose.
CHARACTERS: dict[str, str] = {
    "sora": "Tokino Sora",
    "roboco": "Roboco",
    "miko": "Sakura Miko",
    "suisei": "Hoshimachi Suisei",
    "azki": "AZKi",
    "mel": "Yozora Mel",
    "fubuki": "Shirakami Fubuki",
    "matsuri": "Natsuiro Matsuri",
    "aki": "Aki Rosenthal",
    "haato": "Akai Haato",
    "aqua": "Minato Aqua",
    "shion": "Murasaki Shion",
    "ayame": "Nakiri Ayame",
    "choco": "Yuzuki Choco",
    "subaru": "Oozora Subaru",
    "mio": "Ookami Mio",
    "okayu": "Nekomata Okayu",
    "korone": "Inugami Korone",
    "pekora": "Usada Pekora",
    "flare": "Shiranui Flare",
    "noel": "Shirogane Noel",
    "marine": "Houshou Marine",
    "kanata": "Amane Kanata",
    "coco": "Kiryu Coco",
    "watame": "Tsunomaki Watame",
    "towa": "Tokoyami Towa",
    "luna": "Himemori Luna",
    "calli": "Mori Calliope",
    "kiara": "Takanashi Kiara",
    "ina": "Ninomae Ina'nis",
    "gura": "Gawr Gura",
    "ame": "Watson Amelia",
    "irys": "IRyS",
    "fauna": "Ceres Fauna",
    "kronii": "Ouro Kronii",
    "mumei": "Nanashi Mumei",
    "bae": "Hakos Baelz",
    "sana": "Tsukumo Sana",
    "risu": "Ayunda Risu",
    "moona": "Moona Hoshinova",
    "iofi": "Airani Iofifteen",
    "ollie": "Kureiji Ollie",
    "anya": "Anya Melfissa",
    "reine": "Pavolia Reine",
    "zeta": "Vestia Zeta",
    "kaela": "Kaela Kovalskia",
    "kobo": "Kobo Kanaeru",
}

# --- Unlockable content -------------------------------------------------------
# Basic weapons (the `unlockedWeapons` array of any-character weapons).
WEAPONS: list[str] = [
    "PsychoAxe", "Glowstick", "SpiderCooking", "Tailplug", "BLBook",
    "EliteLava", "HoloBomb", "HoloLaser", "WamyWater", "CEOTears",
    "ENCurse", "CuttingBoard", "BounceBall", "IdolSong", "XPotato",
    "Sausage", "OwlDagger",
]

ITEMS: list[str] = [
    "BodyPillow", "FullMeal", "PikiPikiPiman", "SuccubusHorn", "Headphones",
    "UberSheep", "HolyMilk", "Sake", "FaceMask", "SuperChattoTime",
    "CreditCard", "PiggyBank", "IdolCostume", "ChickensFeather", "StudyGlasses",
    "GorillasPaw", "Halu", "InjectionAsacoco", "Membership", "BlacksmithsGear",
    "Breastplate", "DevilHat", "Bandaid", "Limiter", "GWSPill", "EnergyDrink",
    "HopeSoda", "Plushie", "Shacklesss", "LabCoat", "Candy", "Beetle",
    "NinjaHeadband", "FocusShades",
]

COLLABS: list[str] = [
    "EliteCooking", "BLLover", "BreatheInAsacoco", "DragonBeam", "MariLamy",
    "MiComet", "BrokenDreams", "EldritchHorror", "FlatBoard", "RingOfFitness",
    "BoneBros", "AbsoluteWall", "LightBeam", "IdolConcert", "SnowSake",
    "RapDog", "MiKorone", "CurseBall", "SnowQueen", "StarHalberd", "ImDie",
    "KanaCoco", "IdolLive", "LegendarySausage", "LightningWeiner",
    "StreamOfTears", "Jingisukan", "BloodLust", "BlackPlague",
]

OUTFITS: list[str] = [
    "default", "ameAlt1", "ameAlt2", "ameAlt3", "inaAlt1", "inaAlt2", "inaAlt3",
    "guraAlt1", "guraAlt2", "guraAlt3", "calliAlt1", "calliAlt2", "calliAlt3",
    "kiaraAlt1", "kiaraAlt2", "kiaraAlt3", "kroniiAlt1", "kroniiAlt2",
    "irysAlt1", "irysAlt2", "irysAlt3", "sanaAlt1", "kurokami", "azkiAlt1",
    "azkiAlt2", "suiseiAlt1", "suiseiAlt2", "akiAlt1", "melAlt1", "chocoAlt1",
    "aquaAlt1", "faunaAlt1", "faunaAlt2", "koroneAlt1", "koroneAlt2",
    "okayuAlt1", "okayuAlt2", "mumeiAlt1", "mumeiAlt2", "mikoAlt1", "mikoAlt2",
    "soraAlt1", "soraAlt2", "haatoAlt1", "shionAlt1", "ayameAlt1", "baeAlt1",
    "baeAlt2", "mioAlt1", "mioAlt2", "fubukiAlt1", "fubukiAlt2", "robocoAlt1",
    "robocoAlt2", "matsuriAlt1", "subaruAlt1", "marineAlt1", "flareAlt1",
    "kanataAlt1", "noelAlt1", "pekoraAlt1",
]

STAGES: list[str] = [
    "STAGE 1", "STAGE 2", "STAGE 3", "STAGE 4", "STAGE 5",
    "STAGE 1 (HARD)", "STAGE 2 (HARD)", "STAGE 3 (HARD)", "STAGE 4 (HARD)",
    "STAGE 5 (HARD)", "TIME STAGE 1", "HOLO HOUSE", "USADA CASINO", "DUNGEON",
]

# Which top-level array each unlock category maps to in the save.
UNLOCK_ARRAYS: dict[str, str] = {
    "Weapons": "unlockedWeapons",
    "Items": "unlockedItems",
    "Outfits": "unlockedOutfits",
    "Collabs": "seenCollabs",
    "Stages": "unlockedStages",
    "Furniture": "unlockedFurniture",
}

# Curated master list per category (Furniture intentionally empty -> seeded from
# the save, since the full furniture catalogue is large and cosmetic).
UNLOCK_MASTER: dict[str, list[str]] = {
    "Weapons": WEAPONS,
    "Items": ITEMS,
    "Outfits": OUTFITS,
    "Collabs": COLLABS,
    "Stages": STAGES,
    "Furniture": [],
}

_PRETTY_OVERRIDES = {
    "BLBook": "BL Book",
    "BLLover": "BL Lover",
    "CEOTears": "CEO's Tears",
    "ENCurse": "EN's Curse",
    "GWSPill": "GWS Pill",
    "XPotato": "X-Potato",
    "default": "Default",
    "kurokami": "Kurokami (Fubuki)",
}


def prettify(identifier: str) -> str:
    """Human-readable label for an internal ID (camelCase / alt-suffix aware)."""
    if identifier in _PRETTY_OVERRIDES:
        return _PRETTY_OVERRIDES[identifier]
    if identifier.isupper() or " " in identifier:
        return identifier  # already a display string, e.g. "STAGE 1", "SCT"
    # Split camelCase and trailing digits: "guraAlt1" -> "Gura Alt 1".
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", identifier)
    spaced = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", spaced)
    return spaced[:1].upper() + spaced[1:]
