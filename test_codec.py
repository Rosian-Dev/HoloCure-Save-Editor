"""Correctness checks for save_codec: the round trip must not corrupt data."""

from __future__ import annotations

import sys
from pathlib import Path

import save_codec

SAVE = Path(__file__).parent / "Save" / "save_n.dat"


def test_roundtrip_data_preserved() -> None:
    assert SAVE.exists(), f"sample save missing: {SAVE}"
    assert save_codec.roundtrip_data_equal(SAVE), (
        "decode -> encode -> decode changed the parsed save data"
    )


def test_load_exposes_known_fields() -> None:
    save = save_codec.load_save(SAVE)
    assert "holoCoins" in save.data
    assert isinstance(save.data["holoCoins"], float)
    assert isinstance(save.data["achievements"], dict)
    assert isinstance(save.data["characters"], list)


def test_coerce_like_preserves_type() -> None:
    assert save_codec.coerce_like(1.0, 5) == 5.0
    assert isinstance(save_codec.coerce_like(1.0, 5), float)
    assert save_codec.coerce_like(True, 1) is True
    assert save_codec.coerce_like(False, 0) is False
    assert isinstance(save_codec.coerce_like(3, "7"), int)


def test_write_save_backs_up_beside_save_by_default() -> None:
    import base64
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "save_n.dat"
        save = save_codec.SaveFile(prefix="", data={"holoCoins": 1.0})
        target.write_bytes(save_codec.encode(save))  # pre-existing file
        original_bytes = target.read_bytes()

        save.data["holoCoins"] = 2.0
        backup = save_codec.write_save(save, target)  # no backup_root given

        assert backup is not None and backup.exists()
        assert backup.parent == target.parent / "backups"
        assert backup.read_bytes() == original_bytes      # backup = old content
        assert target.read_bytes() != original_bytes      # target = new content
        # And the new file still decodes to the edited data.
        assert save_codec.load_save(target).data["holoCoins"] == 2.0


def test_write_save_backup_root_is_separate_from_target() -> None:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        game_dir = Path(d) / "HoloCure"
        game_dir.mkdir()
        target = game_dir / "save_n.dat"
        proj = Path(d) / "project"
        proj.mkdir()

        save = save_codec.SaveFile(prefix="", data={"holoCoins": 1.0})
        target.write_bytes(save_codec.encode(save))
        old = target.read_bytes()

        save.data["holoCoins"] = 5.0
        backup = save_codec.write_save(save, target, backup_root=proj)

        # Backup goes to the project root, NOT next to the target.
        assert backup is not None and backup.parent == proj / "backups"
        assert backup.read_bytes() == old
        assert save_codec.load_save(target).data["holoCoins"] == 5.0
        assert not (game_dir / "backups").exists()


def _run() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:  # noqa: BLE001 - simple test runner
                failures += 1
                print(f"FAIL {name}: {exc}")
    print(f"\n{('OK' if not failures else str(failures) + ' FAILED')}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
