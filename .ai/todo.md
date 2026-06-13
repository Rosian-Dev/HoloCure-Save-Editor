# HoloCure Save Editor — Todo

## Plan
- [x] Decode + understand save format (base64 minified JSON; mixed bool encoding)
- [x] `save_codec.py` — load / serialize / timestamped backup / type-preserving coerce
- [x] `test_codec.py` — round-trip data equality + coercion
- [x] `game_data.py` — master ID lists, display names, field labels
- [x] `editor_model.py` — GUI-free edit logic (currency/stats/characters/unlocks/achievements)
- [x] `test_model.py` — edit logic + encoding preservation
- [x] `holocure_editor.py` — CustomTkinter GUI (tabs: Currency/Stats/Characters/Unlocks/Achievements)
- [x] `requirements.txt`, `README.md`, `.gitignore`
- [x] Run `python test_codec.py` (3/3 PASS) and `python test_model.py` (5/5 PASS)
- [x] Build standalone .exe (`build_exe.py` → `dist/HoloCure Save Editor.exe`, 29.7 MB, launches OK)
- [x] Fix APP_ROOT for frozen builds (use sys.executable dir so backups land next to .exe)
- [ ] Manual GUI smoke test (open Save/save_n.dat, edit holoCoins + toggle, Save, confirm backup)
- [ ] In-game load test of an edited save

## Review
- Save = base64 of minified JSON. Output is **not** byte-identical to original
  (GameMaker writes 17-digit floats, Python writes shortest) but is semantically
  identical, so the game loads it. Tests assert semantic equality.
- Encoding fidelity handled via `coerce_like(old, new)` on every write; achievements
  keep per-entry bool-vs-float encoding.
- Master lists are a floor: unioned at runtime with IDs present in the loaded save,
  so newer/unknown content is never hidden. Achievements + roster derived from save.
- Backups: `<project root>/backups/save_n_YYYYMMDD_HHMMSS.dat` before each write.
