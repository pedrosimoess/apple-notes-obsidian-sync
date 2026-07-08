# apple-notes-obsidian-sync

One-way sync (Apple Notes -> Obsidian) for a set of Notes.app folders that
were exported into an Obsidian vault. If you edit a note directly in
Notes.app (Mac or iPhone, synced through iCloud), this script updates the
matching `.md` file in your vault on the next run. It does **not** write
back to Notes.app — edits made only in Obsidian (like the `tags:` field)
are left untouched by this script and are not pushed to Notes.app.

No external dependencies — Python 3.8+ standard library only.

## How it works

1. Reads every note in a fixed set of Notes.app folders (skips `Senhas`
   and `Recently Deleted` on purpose) via AppleScript (`osascript`).
2. Matches each note to its `.md` file in the vault using Apple Notes'
   internal note ID, embedded in the filename as `Title (id).md`.
3. If the note changed (different `modified` date) or is new, it
   rewrites the `.md` file's body, `created`/`modified` frontmatter, and
   renames it if the title changed — while preserving any extra
   frontmatter lines you added yourself (like `tags:`).
4. If a previously-tracked note disappears from Notes.app (deleted or
   moved out of a tracked folder), the file is moved to
   `_Removidos-do-AppleNotes/` inside the vault instead of being deleted.
5. Logs a summary to `Logs/sync_YYYY-MM.log` on every run.

## Requirements

- macOS with the Notes.app signed into the same iCloud account as the
  notes you want to sync
- Python 3.8+ (comes with macOS)
- The Obsidian vault must already have the `Apple Notes/` folder
  structure this script expects (see the `apple-notes-obsidian-sync`
  export this project was built alongside)

## Configuration

Personal settings (vault path, Notes.app account name, folder names, and
your tag taxonomy) live in `config.py`, which is **gitignored** and never
committed — this is what keeps the folder/tag structure private while
the sync logic itself stays public.

```bash
cp config.example.py config.py
```

Then edit `config.py`:

| Variable                 | What it is                                          |
|---------------------------|-----------------------------------------------------|
| `VAULT_APPLE_NOTES_DIR`    | Path to the `Apple Notes/` folder inside your vault  |
| `ACCOUNT_NAME`             | Notes.app account name (sidebar in Notes.app)        |
| `EXCLUDED_FOLDERS`         | Folders to skip (e.g. a passwords folder, trash)     |
| `FOLDER_DEFAULT_TAGS`      | Tag applied to brand-new notes, per folder           |

`notes_sync.py` itself has no personal data in it — safe to keep public.

## Quick start

```bash
git clone https://github.com/pedrosimoess/apple-notes-obsidian-sync.git
cd apple-notes-obsidian-sync
cp config.example.py config.py   # then edit config.py
python3 notes_sync.py
```

The first run will trigger a macOS permission prompt for Terminal/Python
to control Notes.app (System Settings → Privacy & Security → Automation).

## Scheduling (macOS / launchd)

See `agendamento/macos/LEIAME.md` for installing the included
`.plist` to run this automatically every 30 minutes.

## Notes

- A note's tag is never assigned automatically for existing notes — this
  script only preserves whatever `tags:` is already in the file. New
  notes get a default tag based on which Notes.app folder they're in
  (see `FOLDER_DEFAULT_TAGS`); the "Notes" catch-all folder defaults new
  notes to `diversos` since content-based classification was done by
  hand and isn't replicated here.
- State (last-seen modification date per note) is kept in
  `.sync_state.json`, gitignored — delete it to force a full re-scan.
