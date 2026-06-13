"""Load, serialize and back up HoloCure save files.

A HoloCure ``save_n.dat`` is base64 of a *minified* JSON object produced by
GameMaker. Two details matter for not corrupting saves:

* It is minified (no spaces) -> serialize with ``separators=(",", ":")``.
* It mixes real JSON ``true``/``false`` with GameMaker ``1.0``/``0.0`` floats,
  even inside the same structure. Python's ``json`` round-trips these by *type*
  (bool stays bool, float stays float, whole floats keep their ``.0``), so as
  long as every edited value keeps the original field's type the encoding is
  preserved. Use :func:`coerce_like` for that.

Some saves carry a PC/Steam identifier prefix before the JSON; we locate the
first ``{"`` and preserve whatever comes before it verbatim.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SaveFile:
    """A decoded save: any text ``prefix`` before the JSON, plus the data."""

    prefix: str
    data: dict
    path: Path | None = None


def _find_json_start(text: str) -> int:
    """Index of the JSON object start, tolerating a space after the brace."""
    idx = text.find('{"')
    if idx == -1:
        idx = text.find('{ "')
    if idx == -1:
        raise ValueError("No JSON object found in decoded save data.")
    return idx


def load_save(path: str | Path) -> SaveFile:
    """Decode ``path`` (base64) into a :class:`SaveFile`."""
    path = Path(path)
    raw = path.read_bytes()
    text = base64.b64decode(raw).decode("utf-8", errors="strict")
    idx = _find_json_start(text)
    prefix = text[:idx]
    data = json.loads(text[idx:])
    return SaveFile(prefix=prefix, data=data, path=path)


def dumps(save: SaveFile) -> str:
    """Serialize back to the exact on-disk text (prefix + minified JSON)."""
    body = json.dumps(save.data, separators=(",", ":"), ensure_ascii=False)
    return save.prefix + body


def encode(save: SaveFile) -> bytes:
    """Serialize and base64-encode, ready to write to ``save_n.dat``."""
    return base64.b64encode(dumps(save).encode("utf-8"))


def backup_existing(target: str | Path, backup_root: str | Path | None = None) -> Path | None:
    """Copy an existing ``target`` into a ``backups`` folder (timestamped).

    The ``backups`` folder is created under ``backup_root`` if given, otherwise
    next to ``target`` itself. We back up next to the save (a normal writable
    user-data folder) rather than next to a frozen .exe: writing into a
    PyInstaller one-file exe's own directory is unreliable on Windows.

    A plain byte copy is used (not ``shutil.copy2``): copying file *metadata*
    via Windows APIs fails inside the frozen exe, and a backup needs only the
    bytes.

    Returns the backup path, or ``None`` if ``target`` did not exist.
    """
    target = Path(target)
    if not target.exists():
        return None
    base = Path(backup_root) if backup_root is not None else target.parent
    backups_dir = base / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backups_dir / f"{target.stem}_{stamp}{target.suffix}"
    # Avoid clobbering if two saves happen within the same second.
    counter = 1
    while dest.exists():
        dest = backups_dir / f"{target.stem}_{stamp}_{counter}{target.suffix}"
        counter += 1
    dest.write_bytes(target.read_bytes())
    return dest


def write_save(save: SaveFile, target: str | Path, backup_root: str | Path | None = None) -> Path | None:
    """Back up any existing file at ``target`` then write ``save`` to it.

    ``backup_root`` is where the ``backups`` folder is created; when omitted it
    defaults to the save file's own directory.

    Returns the backup path that was created (or ``None``).
    """
    target = Path(target)
    backup = backup_existing(target, backup_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encode(save))
    return backup


def coerce_like(old_value, new_value):
    """Return ``new_value`` typed like ``old_value`` to preserve encoding.

    ``bool`` is checked before ``int``/``float`` because ``bool`` is a subclass
    of ``int`` in Python.
    """
    if isinstance(old_value, bool):
        return bool(new_value)
    if isinstance(old_value, float):
        return float(new_value)
    if isinstance(old_value, int):
        return int(new_value)
    if isinstance(old_value, str):
        return str(new_value)
    return new_value


def roundtrip_data_equal(path: str | Path) -> bool:
    """True if decode -> encode -> decode preserves the data exactly.

    Note: byte-for-byte identity is *not* achievable, because GameMaker writes
    floats at full 17-digit precision (e.g. ``0.69999999999999996``) while
    Python emits the shortest round-tripping form (``0.7``). Both parse to the
    same IEEE-754 double, so the game loads either identically. The meaningful
    guarantee is therefore semantic (parsed-data) equality, which this checks.
    """
    path = Path(path)
    original = load_save(path)
    reparsed = json.loads(dumps(original)[len(original.prefix):])
    return reparsed == original.data
