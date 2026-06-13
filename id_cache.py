"""Persistent, append-only cache of known content IDs (names only).

The editor's curated master lists are a *floor*. As HoloCure updates add new
weapons/items/outfits/characters/etc., opening a save that contains them records
those new IDs here so they remain listed in future sessions. Entries are never
removed — the cache only grows.

Stored as JSON next to the app:  ``id_cache.json``
``{ "Weapons": [...], "Items": [...], ... }``  (ids/names only, no values)
"""

from __future__ import annotations

import json
from pathlib import Path


class IdCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: dict[str, list[str]] = {}
        self._dirty = False
        self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self.data = {
                    k: list(v) for k, v in raw.items() if isinstance(v, list)
                }
        except (FileNotFoundError, ValueError, OSError):
            self.data = {}

    def get(self, category: str) -> list[str]:
        return list(self.data.get(category, []))

    def merge(self, category: str, ids: list[str]) -> list[str]:
        """Add any unseen ``ids`` to ``category`` (append, preserve order).

        Returns the full ordered list for the category after merging.
        """
        existing = self.data.setdefault(category, [])
        known = set(existing)
        added = [i for i in ids if i not in known]
        if added:
            existing.extend(added)
            self._dirty = True
        return list(existing)

    def save(self) -> None:
        if not self._dirty:
            return
        try:
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._dirty = False
        except OSError:
            pass  # cache is best-effort; never block editing on a cache write
