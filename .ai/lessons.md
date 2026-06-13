# Lessons

## HoloCure save format
- `save_n.dat` is base64 of **minified** JSON (no spaces) → serialize with
  `json.dumps(data, separators=(",", ":"))`.
- A PC/Steam identifier may precede the JSON. Locate the first `{"` and preserve
  the prefix verbatim.
- Booleans are encoded inconsistently: real JSON `true`/`false` AND GameMaker
  `1.0`/`0.0`, even within the same `achievements.*.unlocked` field. Preserve each
  field's original Python type on write (`coerce_like`). Never normalize globally.
- GameMaker writes floats at full precision (`0.69999999999999996`); Python writes
  the shortest form (`0.7`). Both parse to the same double. Test for **semantic**
  (parsed-data) equality, not byte equality.

## Environment
- This harness blocks running interpreters with a script (`python file.py`,
  `python -c`, `node -e`, PowerShell script blocks) behind a manual-approval gate
  that may not auto-grant. Plain `python --version` and `base64 -d | head/tail`
  pipes are allowed. To inspect a binary save, decode in chunks with
  `base64 -d FILE | tail -c +N | head -c M` instead of an interpreter one-liner.
- **PyInstaller one-file exe: do NOT write into the exe's own folder.** Writing
  files next to a frozen one-file .exe (`Path(sys.executable).parent`) fails on
  Windows — `shutil.copy2` dies in Windows metadata APIs (WinError 2, filename
  None) and even plain `write_bytes` into that dir can ENOENT. Write user data to
  a normal location instead: backups beside the save file, app data under
  `%LOCALAPPDATA%\<App>`. Verified by building tiny probe exes and reading a log.
- For backups, prefer a plain byte copy (`dst.write_bytes(src.read_bytes())`)
  over `shutil.copy2` — copy2's metadata copy is what breaks when frozen.
- Reference data: `araguma/holocure-save-editor` `src/versions/0.5/save.ts` has ID
  enums (older v0.5 set). The live save itself is the most complete source for its
  own version (achievements + full roster are always present).
