"""Editing logic checks that don't need a GUI or the real save file."""

from __future__ import annotations

import sys

import tempfile
from pathlib import Path

from editor_model import EditorModel
from id_cache import IdCache
from save_codec import SaveFile


def _model() -> EditorModel:
    data = {
        "holoCoins": 100.0,
        "ATK": 1.0,
        "characters": [["gura", 5.0], ["random", 0.0]],
        "fandomEXP": [["gura", 10.0]],
        "characterClears": [],
        "unlockedWeapons": ["HoloBomb"],
        "achievements": {
            "boolAch": {"unlocked": False, "flags": {}},
            "numAch": {"unlocked": 1.0, "flags": {}},
        },
    }
    return EditorModel(SaveFile(prefix="", data=data))


def test_number_keeps_float_type() -> None:
    m = _model()
    m.set_number("holoCoins", 999999)
    assert m.data["holoCoins"] == 999999.0
    assert isinstance(m.data["holoCoins"], float)


def test_character_roster_excludes_meta() -> None:
    m = _model()
    assert m.character_ids() == ["gura"]


def test_set_character_updates_pairs_and_adds_clears() -> None:
    m = _model()
    m.set_character("gura", level=42, fandom_exp=80, clears=3)
    assert m.data["characters"][0] == ["gura", 42.0]
    assert m.data["fandomEXP"][0] == ["gura", 80.0]
    assert m.data["characterClears"] == [["gura", 3.0]]


def test_unlock_union_and_toggle() -> None:
    m = _model()
    opts = m.unlock_options("Weapons")
    assert "HoloBomb" in opts and "PsychoAxe" in opts  # save id + master id
    assert m.is_unlocked("Weapons", "HoloBomb")
    m.set_unlocked("Weapons", "HoloBomb", False)
    assert not m.is_unlocked("Weapons", "HoloBomb")
    m.set_unlocked("Weapons", "PsychoAxe", True)
    assert "PsychoAxe" in m.data["unlockedWeapons"]


def test_achievement_encoding_preserved() -> None:
    m = _model()
    m.set_achievement("boolAch", True)
    m.set_achievement("numAch", False)
    assert m.data["achievements"]["boolAch"]["unlocked"] is True  # stays bool
    num = m.data["achievements"]["numAch"]["unlocked"]
    assert num == 0.0 and isinstance(num, float)  # stays float


def test_id_cache_is_append_only() -> None:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "id_cache.json"
        c = IdCache(path)
        assert c.merge("Weapons", ["A", "B"]) == ["A", "B"]
        c.save()
        # New session sees old ids; adding a new one appends, never drops.
        c2 = IdCache(path)
        assert c2.get("Weapons") == ["A", "B"]
        assert c2.merge("Weapons", ["B", "C"]) == ["A", "B", "C"]
        # A shorter later listing must not remove previously-seen ids.
        assert c2.merge("Weapons", ["A"]) == ["A", "B", "C"]


def _run() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {exc}")
    print(f"\n{('OK' if not failures else str(failures) + ' FAILED')}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
