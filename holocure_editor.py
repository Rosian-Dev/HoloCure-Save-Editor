"""HoloCure Save Editor — CustomTkinter GUI.

Run:  python holocure_editor.py
Requires:  customtkinter  (pip install -r requirements.txt)
"""

from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - friendly message instead of a traceback
    sys.exit(
        "customtkinter is not installed.\n"
        "Install it with:  pip install -r requirements.txt\n"
        "(or:  pip install customtkinter)"
    )

import game_data
from editor_model import EditorModel
from id_cache import IdCache


def _app_root() -> Path:
    """Folder the app lives in.

    When frozen by PyInstaller, ``__file__`` points at a temp extraction dir, so
    use the executable's location instead.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_ROOT = _app_root()


def _data_dir() -> Path:
    """Writable per-user folder for app data (the id cache).

    Writing into a frozen one-file exe's own directory is unreliable on Windows,
    so keep persistent app data under ``%LOCALAPPDATA%\\HoloCureSaveEditor``,
    falling back to the app folder only if that can't be created.
    """
    local = os.environ.get("LOCALAPPDATA")
    if local:
        base = Path(local) / "HoloCureSaveEditor"
        try:
            base.mkdir(parents=True, exist_ok=True)
            return base
        except OSError:
            pass
    return APP_ROOT


def _game_save() -> Path:
    """The save file the game actually loads: ``%LOCALAPPDATA%\\HoloCure\\save_n.dat``.

    Saving always targets this file (regardless of what was opened) so edits
    land where the game reads them.
    """
    local = os.environ.get("LOCALAPPDATA") or str(APP_ROOT)
    return Path(local) / "HoloCure" / "save_n.dat"


def _project_root() -> Path:
    """Project folder that holds the ``backups`` directory.

    When frozen the exe lives in ``…\\dist``; backups belong one level up in the
    project root next to it. In dev, ``APP_ROOT`` is already the project root.
    """
    return APP_ROOT.parent if APP_ROOT.name.lower() == "dist" else APP_ROOT


GAME_SAVE = _game_save()
BACKUP_ROOT = _project_root()
DEFAULT_SAVE = GAME_SAVE  # the Open dialog points here by default


def num_to_str(value) -> str:
    """Show whole floats without a trailing ``.0`` for a cleaner UI."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def holocure_running() -> bool:
    """True if the HoloCure game process appears to be running (Windows).

    If the game is open, the on-disk save is a stale snapshot (the game holds
    currency etc. in memory and only flushes periodically), and any edits we
    write will be overwritten when the game next saves or exits. Best-effort:
    failures are treated as "not running" so detection never blocks editing.
    """
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/fi", "imagename eq HoloCure.exe", "/nh"],
            capture_output=True, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return "HoloCure.exe" in out.stdout
    except Exception:  # noqa: BLE001 - detection is advisory only
        return False


class HoloCureEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HoloCure Save Editor")
        self.geometry("960x720")
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.model: EditorModel | None = None
        self.save_path: Path | None = None
        self.cache = IdCache(_data_dir() / "id_cache.json")

        # Widget registries, rebuilt on each load.
        self._number_entries: dict[str, ctk.CTkEntry] = {}
        self._character_entries: dict[str, dict[str, ctk.CTkEntry]] = {}
        self._character_rows: dict[str, dict] = {}
        self._char_search_var: ctk.StringVar | None = None
        self._unlock_vars: dict[str, dict[str, ctk.BooleanVar]] = {}
        self._achievement_vars: dict[str, ctk.BooleanVar] = {}

        self._build_toolbar()
        self._build_tabs()
        self._set_status("Open a save file to begin.")

    # --- top toolbar ---------------------------------------------------------
    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(self)
        bar.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkButton(bar, text="Load Save", width=110,
                      command=self.open_game_save).pack(side="left", padx=(8, 4), pady=8)
        ctk.CTkButton(bar, text="Open…", width=80, command=self.open_file).pack(
            side="left", padx=4, pady=8
        )
        self.reload_button = ctk.CTkButton(
            bar, text="Reload", width=80, command=self.reload_file, state="disabled"
        )
        self.reload_button.pack(side="left", padx=4, pady=8)
        self.save_button = ctk.CTkButton(
            bar, text="Save", width=90, command=self.save_file, state="disabled"
        )
        self.save_button.pack(side="left", padx=4, pady=8)

        self.path_label = ctk.CTkLabel(bar, text="No file loaded", anchor="w")
        self.path_label.pack(side="left", padx=12, fill="x", expand=True)

        self.status_label = ctk.CTkLabel(self, text="", anchor="w", text_color="gray")
        self.status_label.pack(fill="x", padx=18, pady=(2, 0))

    def _build_tabs(self) -> None:
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        for name in ("Currency", "Stats", "Characters", "Unlocks", "Achievements"):
            self.tabs.add(name)

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status_label.configure(
            text=text, text_color=("#c0392b" if error else "gray")
        )

    # --- file actions --------------------------------------------------------
    def open_game_save(self) -> None:
        """Open the game's real save directly (no dialog)."""
        if not GAME_SAVE.exists():
            messagebox.showerror(
                "Game save not found",
                f"Could not find the HoloCure save at:\n{GAME_SAVE}\n\n"
                "Use 'Open…' to locate it manually.",
            )
            return
        self._load_path(GAME_SAVE)

    def open_file(self) -> None:
        initial = DEFAULT_SAVE if DEFAULT_SAVE.exists() else APP_ROOT
        path = filedialog.askopenfilename(
            title="Open HoloCure save",
            initialdir=initial.parent if initial.is_file() else initial,
            initialfile=initial.name if initial.is_file() else "",
            filetypes=[("HoloCure save", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return
        self._load_path(Path(path))

    def reload_file(self) -> None:
        """Re-read the currently open file from disk (discards unsaved edits)."""
        if not self.save_path:
            return
        if not messagebox.askokcancel(
            "Reload save",
            "Re-read the file from disk?\n\nAny unsaved changes in the editor "
            "will be discarded.",
        ):
            return
        self._load_path(self.save_path)

    def _load_path(self, path: Path) -> None:
        try:
            self.model = EditorModel.load(path)
        except Exception as exc:  # noqa: BLE001 - surface any decode error to user
            messagebox.showerror("Failed to open save", f"{exc}\n\n{traceback.format_exc()}")
            return
        self.save_path = path
        self.path_label.configure(text=str(self.save_path))
        self.save_button.configure(state="normal")
        self.reload_button.configure(state="normal")
        self._populate_all()
        if holocure_running():
            self._set_status(
                "⚠ HoloCure is running — the on-disk save is stale and may not match "
                "in-game values. Close the game, then Reload.", error=True,
            )
        else:
            self._set_status("Loaded. Make changes, then click Save (a backup is made automatically).")

    def save_file(self) -> None:
        if not self.model or not self.save_path:
            return
        if holocure_running() and not messagebox.askokcancel(
            "HoloCure is running",
            "HoloCure appears to be running.\n\n"
            "If you save now, the game will overwrite your changes the next time "
            "it autosaves or when you close it.\n\n"
            "Close HoloCure first for changes to stick. Save anyway?",
            icon="warning",
        ):
            self._set_status("Save cancelled — close HoloCure, then save.", error=True)
            return
        try:
            self._apply_numbers()
            self._apply_characters()
            self._apply_unlocks()
            self._apply_achievements()
        except ValueError as exc:
            self._set_status(str(exc), error=True)
            return
        try:
            # Always write to the game's real save, and back up the pre-edit
            # game save into the project's backups/ folder — regardless of which
            # file was opened.
            backup = self.model.write(GAME_SAVE, backup_root=BACKUP_ROOT)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save failed", f"{exc}\n\n{traceback.format_exc()}")
            return
        where = f"  Backup: {backup}" if backup else "  (no prior game save to back up)"
        self._set_status(f"Saved to {GAME_SAVE}.{where}")

    # --- populate (rebuild tab contents from the model) ----------------------
    def _populate_all(self) -> None:
        self._number_entries.clear()  # avoid stale refs when reopening a file
        self._populate_numbers("Currency", game_data.CURRENCY_FIELDS)
        self._populate_numbers("Stats", game_data.STAT_FIELDS)
        self._populate_characters()
        self._populate_unlocks()
        self._populate_achievements()
        self.cache.save()  # persist any newly-seen ids (append-only)

    @staticmethod
    def _clear(frame: ctk.CTkBaseClass) -> None:
        for child in frame.winfo_children():
            child.destroy()

    def _populate_numbers(self, tab: str, fields: dict[str, str]) -> None:
        frame = self.tabs.tab(tab)
        self._clear(frame)
        scroll = ctk.CTkScrollableFrame(frame)
        scroll.pack(fill="both", expand=True, padx=6, pady=6)
        scroll.grid_columnconfigure(1, weight=1)
        row = 0
        for key, label in fields.items():
            if not self.model.has_field(key):
                continue
            ctk.CTkLabel(scroll, text=label, anchor="w").grid(
                row=row, column=0, sticky="w", padx=(6, 12), pady=4
            )
            entry = ctk.CTkEntry(scroll, width=180)
            entry.insert(0, num_to_str(self.model.get_number(key)))
            entry.grid(row=row, column=1, sticky="w", pady=4)
            self._number_entries[key] = entry
            row += 1
        if row == 0:
            ctk.CTkLabel(scroll, text="No matching fields in this save.").grid(row=0, column=0)

    def _populate_characters(self) -> None:
        frame = self.tabs.tab("Characters")
        self._clear(frame)
        self._character_entries.clear()
        self._character_rows.clear()

        # Record the roster in the append-only cache (names only).
        self.cache.merge("Characters", self.model.character_ids())

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=6, pady=(6, 0))
        ctk.CTkLabel(top, text="Search:").pack(side="left", padx=(6, 6), pady=6)
        self._char_search_var = ctk.StringVar()
        self._char_search_var.trace_add("write", lambda *_: self._filter_characters())
        ctk.CTkEntry(top, textvariable=self._char_search_var, width=240,
                     placeholder_text="Filter by character name…").pack(
            side="left", padx=4, pady=6
        )
        ctk.CTkButton(top, text="Max EXP (all)", width=120,
                      command=self._set_max_exp_all).pack(side="right", padx=6, pady=6)

        scroll = ctk.CTkScrollableFrame(frame)
        scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self._char_scroll = scroll
        headers = ["Character", "Level", "Fandom EXP", "Clears", ""]
        for col, text in enumerate(headers):
            ctk.CTkLabel(scroll, text=text, font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=col, sticky="w", padx=8, pady=(2, 6)
            )
        for r, cid in enumerate(self.model.character_ids(), start=1):
            name = game_data.CHARACTERS.get(cid, cid)
            widgets = []
            name_label = ctk.CTkLabel(scroll, text=name, anchor="w")
            name_label.grid(row=r, column=0, sticky="w", padx=8, pady=2)
            widgets.append(name_label)
            values = self.model.get_character(cid)
            entries = {}
            for col, field in enumerate(("level", "fandomEXP", "clears"), start=1):
                entry = ctk.CTkEntry(scroll, width=110)
                entry.insert(0, num_to_str(values[field]))
                entry.grid(row=r, column=col, sticky="w", padx=8, pady=2)
                entries[field] = entry
                widgets.append(entry)
            max_btn = ctk.CTkButton(
                scroll, text="Max EXP", width=80,
                command=lambda c=cid: self._set_max_exp(c),
            )
            max_btn.grid(row=r, column=4, sticky="w", padx=8, pady=2)
            widgets.append(max_btn)
            self._character_entries[cid] = entries
            self._character_rows[cid] = {"row": r, "name": name, "widgets": widgets}

    def _set_max_exp(self, cid: str) -> None:
        """Set this character's Fandom EXP entry to the max (100)."""
        entry = self._character_entries[cid]["fandomEXP"]
        entry.delete(0, "end")
        entry.insert(0, "100")

    def _set_max_exp_all(self) -> None:
        """Set every character's Fandom EXP entry to the max (100)."""
        for cid in self._character_entries:
            self._set_max_exp(cid)
        self._set_status("Set Fandom EXP to 100 for all characters. Click Save to apply.")

    def _filter_characters(self) -> None:
        """Show only rows whose character name matches the search text."""
        query = (self._char_search_var.get() if self._char_search_var else "").strip().lower()
        for info in self._character_rows.values():
            visible = query in info["name"].lower()
            for col, widget in enumerate(info["widgets"]):
                if visible:
                    widget.grid(row=info["row"], column=col, sticky="w", padx=8, pady=2)
                else:
                    widget.grid_remove()

    def _populate_unlocks(self) -> None:
        frame = self.tabs.tab("Unlocks")
        self._clear(frame)
        self._unlock_vars.clear()
        inner = ctk.CTkTabview(frame)
        inner.pack(fill="both", expand=True, padx=4, pady=4)
        for category in game_data.UNLOCK_ARRAYS:
            inner.add(category)
            self._build_checklist(
                inner.tab(category),
                options=self._cached_options(category, self.model.unlock_options(category)),
                is_on=lambda ident, c=category: self.model.is_unlocked(c, ident),
                label_fn=game_data.prettify,
                store=self._unlock_vars.setdefault(category, {}),
            )

    def _cached_options(self, category: str, base: list[str]) -> list[str]:
        """``base`` (master+save) plus any previously-cached ids; cache grows."""
        cached = self.cache.get(category)
        options = base + [i for i in cached if i not in base]
        self.cache.merge(category, options)
        return options

    def _populate_achievements(self) -> None:
        frame = self.tabs.tab("Achievements")
        self._clear(frame)
        self._achievement_vars.clear()
        self._build_checklist(
            frame,
            options=self._cached_options("Achievements", self.model.achievement_ids()),
            is_on=self.model.achievement_unlocked,
            label_fn=game_data.prettify,
            store=self._achievement_vars,
        )

    def _build_checklist(self, parent, options, is_on, label_fn, store: dict) -> None:
        controls = ctk.CTkFrame(parent)
        controls.pack(fill="x", padx=4, pady=(4, 0))

        def set_all(value: bool) -> None:
            for var in store.values():
                var.set(value)

        ctk.CTkButton(controls, text="Select all", width=90,
                      command=lambda: set_all(True)).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(controls, text="Clear all", width=90,
                      command=lambda: set_all(False)).pack(side="left", padx=4, pady=4)
        ctk.CTkLabel(controls, text=f"{len(options)} entries").pack(side="left", padx=10)

        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        cols = 3
        for idx, ident in enumerate(options):
            var = ctk.BooleanVar(value=bool(is_on(ident)))
            store[ident] = var
            ctk.CTkCheckBox(scroll, text=label_fn(ident), variable=var).grid(
                row=idx // cols, column=idx % cols, sticky="w", padx=8, pady=3
            )

    # --- apply (read widgets back into the model) ----------------------------
    def _parse_number(self, raw: str, label: str) -> float:
        raw = raw.strip()
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"'{label}' must be a number (got '{raw}').")

    def _apply_numbers(self) -> None:
        all_fields = {**game_data.CURRENCY_FIELDS, **game_data.STAT_FIELDS}
        for key, entry in self._number_entries.items():
            value = self._parse_number(entry.get(), all_fields.get(key, key))
            self.model.set_number(key, value)

    def _apply_characters(self) -> None:
        for cid, entries in self._character_entries.items():
            name = game_data.CHARACTERS.get(cid, cid)
            self.model.set_character(
                cid,
                level=self._parse_number(entries["level"].get(), f"{name} Level"),
                fandom_exp=self._parse_number(entries["fandomEXP"].get(), f"{name} Fandom EXP"),
                clears=self._parse_number(entries["clears"].get(), f"{name} Clears"),
            )

    def _apply_unlocks(self) -> None:
        for category, vars_by_id in self._unlock_vars.items():
            for ident, var in vars_by_id.items():
                self.model.set_unlocked(category, ident, var.get())

    def _apply_achievements(self) -> None:
        for ident, var in self._achievement_vars.items():
            self.model.set_achievement(ident, var.get())


def main() -> None:
    HoloCureEditor().mainloop()


if __name__ == "__main__":
    main()
