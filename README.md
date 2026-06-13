# HoloCure Save Editor

A small desktop GUI for editing HoloCure save files (`save_n.dat`). Edit
currency, permanent upgrade stats, characters (level / fandom EXP / clears), and
unlocks (weapons, items, outfits, collabs, stages, furniture, achievements).

**Saving always writes to the game's real save**,
`%LOCALAPPDATA%\HoloCure\save_n.dat`, no matter which file you opened — so edits
always land where the game reads them. Before overwriting, the current (pre-edit)
game save is copied, timestamped, into the project's `backups/` folder
(`…\HoloCure Save Editor\backups\`) so you can always roll back.

Use **Open Game Save** to load that file directly (one click, no dialog).

## How it works
HoloCure stores `save_n.dat` as **base64 of minified JSON** produced by
GameMaker. The editor:

- decodes base64, preserves any identifier text before the JSON, parses the JSON;
- only rewrites the fields you change, keeping each value's original type so the
  save's mixed encoding (`true`/`false` vs GameMaker `1.0`/`0.0`) is preserved;
- re-serializes minified (`separators=(",", ":")`) and re-encodes to base64.

> Byte-for-byte identical output is not possible (GameMaker writes floats at full
> 17-digit precision, e.g. `0.69999999999999996`; Python writes the shortest
> equivalent, `0.7`). Both parse to the same number, so the game loads either.

## Important: close HoloCure before editing
HoloCure keeps your save (coins, etc.) **in memory** while running and only
writes it to disk periodically and on exit. So while the game is open:

- the on-disk `save_n.dat` the editor reads is a **stale snapshot** that keeps
  changing as you play (values drift up/down as you earn/spend), and
- anything you save will be **overwritten** when the game next autosaves or
  closes.

Always **close HoloCure first**, then open the editor (use **Reload** to re-read
the latest save). The editor warns you if it detects the game running.

## Setup
```sh
pip install -r requirements.txt
```

## Run
```sh
python holocure_editor.py
```
Click **Open…** (defaults to your real save at
`%LOCALAPPDATA%\HoloCure\save_n.dat`, falling back to the bundled
`Save/save_n.dat`), edit, then **Save**.

## Build a standalone .exe (Windows)
No Python needed to *run* the result — just to build it.
```sh
pip install -r requirements-dev.txt
python build_exe.py
```
Produces `dist/HoloCure Save Editor.exe` (single file, no console window).
Put the .exe wherever you like; the `backups/` folder and the default `Save/`
lookup are created **next to the .exe**.

## Tests
```sh
python test_codec.py    # round-trip preserves data; type coercion
python test_model.py     # editing logic + encoding preservation
```

## Files
- `holocure_editor.py` — CustomTkinter GUI (entry point).
- `editor_model.py` — GUI-free editing logic over a loaded save.
- `save_codec.py` — base64/JSON load, serialize, timestamped backup.
- `game_data.py` — master ID lists, display names, field labels.
- `id_cache.py` — append-only `id_cache.json` (next to the app) that records any
  new content IDs seen in opened saves, so future game updates stay listed.

## Notes
- Master ID lists target ~v0.7 and are **unioned with whatever IDs your save
  already contains**, so newer content is never hidden. Achievements and the
  character roster are read directly from your save (complete there).
- The Characters tab is **edit-only** (it never adds characters): use the search
  box to filter by name, the per-row **Max EXP** button to set one character's
  fandom EXP to 100, or **Max EXP (all)** to do it for every character at once.
- Known IDs are cached in `id_cache.json` and only ever grow — new content from
  future updates is recorded the first time you open a save containing it.
- Where to find your real save on Windows:
  `%LOCALAPPDATA%\HoloCure\save_n.dat`. Make a copy before experimenting.
