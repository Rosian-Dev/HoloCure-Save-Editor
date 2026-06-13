"""GUI-free editing logic over a loaded save.

Wraps a :class:`save_codec.SaveFile` and exposes typed getters/setters for the
things the editor touches: currency, upgrade stats, characters, unlock arrays
and achievements. All writes go through :func:`save_codec.coerce_like` so the
save's original encoding (``true``/``false`` vs ``1.0``/``0.0``) is preserved.
"""

from __future__ import annotations

from pathlib import Path

import game_data
import save_codec
from save_codec import SaveFile, coerce_like

# Meta entries in the `characters` array that are not real playable characters.
_META_CHARACTERS = {"random", "none", "empty"}


class EditorModel:
    def __init__(self, save: SaveFile):
        self.save = save

    @classmethod
    def load(cls, path: str | Path) -> "EditorModel":
        return cls(save_codec.load_save(path))

    @property
    def data(self) -> dict:
        return self.save.data

    # --- simple top-level numeric fields (currency + stats) ------------------
    def has_field(self, key: str) -> bool:
        return key in self.data

    def get_number(self, key: str) -> float | int:
        return self.data.get(key, 0)

    def set_number(self, key: str, value: float) -> None:
        if key not in self.data:
            self.data[key] = float(value)
        else:
            self.data[key] = coerce_like(self.data[key], value)

    def worker_coins(self) -> int:
        """Coins currently stored by Holo House workers (collectable).

        Each entry in ``manageWorkers`` is a flat array; index 13 is the worker's
        stored/collectable coins (it drops to 0 right after collecting, while the
        lifetime total at index 14 keeps growing). The game credits these on top
        of ``holoCoins`` when you collect, which is why the in-game total can sit
        above the saved ``holoCoins`` value.
        """
        total = 0.0
        for w in self.data.get("manageWorkers", []):
            if (isinstance(w, list) and len(w) > 13
                    and isinstance(w[13], (int, float)) and not isinstance(w[13], bool)):
                total += w[13]
        return int(total)

    # --- paired [id, value] arrays (characters/fandomEXP/characterClears) ----
    @staticmethod
    def _pair_get(pairs: list, ident: str, default=0.0):
        for entry in pairs:
            if entry and entry[0] == ident:
                return entry[1]
        return default

    @staticmethod
    def _pair_set(pairs: list, ident: str, value) -> None:
        for entry in pairs:
            if entry and entry[0] == ident:
                entry[1] = coerce_like(entry[1], value)
                return
        pairs.append([ident, float(value)])

    def character_ids(self) -> list[str]:
        """Playable character ids present in the save, in save order."""
        out = []
        for entry in self.data.get("characters", []):
            if entry and entry[0] not in _META_CHARACTERS:
                out.append(entry[0])
        return out

    def get_character(self, cid: str) -> dict:
        return {
            "level": self._pair_get(self.data.get("characters", []), cid, 0.0),
            "fandomEXP": self._pair_get(self.data.get("fandomEXP", []), cid, 0.0),
            "clears": self._pair_get(self.data.get("characterClears", []), cid, 0.0),
        }

    def set_character(self, cid: str, level=None, fandom_exp=None, clears=None) -> None:
        if level is not None:
            self._pair_set(self.data.setdefault("characters", []), cid, level)
        if fandom_exp is not None:
            self._pair_set(self.data.setdefault("fandomEXP", []), cid, fandom_exp)
        if clears is not None:
            self._pair_set(self.data.setdefault("characterClears", []), cid, clears)

    # --- unlock arrays -------------------------------------------------------
    def unlock_options(self, category: str) -> list[str]:
        """Curated master list unioned with ids actually present in the save."""
        array_key = game_data.UNLOCK_ARRAYS[category]
        present = self.data.get(array_key, [])
        master = game_data.UNLOCK_MASTER.get(category, [])
        ordered = list(master)
        for ident in present:
            if ident not in ordered:
                ordered.append(ident)
        return ordered

    def is_unlocked(self, category: str, ident: str) -> bool:
        array_key = game_data.UNLOCK_ARRAYS[category]
        return ident in self.data.get(array_key, [])

    def set_unlocked(self, category: str, ident: str, unlocked: bool) -> None:
        array_key = game_data.UNLOCK_ARRAYS[category]
        arr = self.data.setdefault(array_key, [])
        if unlocked and ident not in arr:
            arr.append(ident)
        elif not unlocked and ident in arr:
            arr[:] = [i for i in arr if i != ident]

    # --- achievements --------------------------------------------------------
    def achievement_ids(self) -> list[str]:
        return sorted(self.data.get("achievements", {}).keys())

    def achievement_unlocked(self, ident: str) -> bool:
        entry = self.data.get("achievements", {}).get(ident, {})
        return bool(entry.get("unlocked"))

    def set_achievement(self, ident: str, unlocked: bool) -> None:
        achievements = self.data.setdefault("achievements", {})
        entry = achievements.get(ident)
        if entry is None:
            # New entry: default to GameMaker numeric encoding used by the game.
            achievements[ident] = {"unlocked": 1.0 if unlocked else 0.0, "flags": {}}
            return
        old = entry.get("unlocked", 0.0)
        entry["unlocked"] = coerce_like(old, 1 if unlocked else 0)

    # --- persistence ---------------------------------------------------------
    def write(self, target: str | Path, backup_root: str | Path | None = None) -> Path | None:
        return save_codec.write_save(self.save, target, backup_root)
