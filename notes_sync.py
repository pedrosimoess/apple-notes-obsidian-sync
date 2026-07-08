#!/usr/bin/env python3
"""
apple-notes-obsidian-sync

Sentido único: Apple Notes (conta iCloud) -> Obsidian Vault.
Roda por cima das notas exportadas em julho/2026. Se você editar uma nota
direto no Notes.app (Mac ou iPhone, via iCloud), este script atualiza o
.md correspondente no vault na próxima execução. NÃO escreve de volta no
Notes.app -- edições feitas só no Obsidian (como a tag: que você adicionou)
não são tocadas por este script, mas também não são enviadas ao Notes.app.

Zero dependências externas -- só biblioteca padrão do Python.
"""

import glob
import json
import os
import subprocess
import sys
from datetime import datetime

try:
    from config import (
        VAULT_APPLE_NOTES_DIR,
        ACCOUNT_NAME,
        EXCLUDED_FOLDERS,
        FOLDER_DEFAULT_TAGS,
    )
except ImportError:
    print(
        "Arquivo config.py não encontrado.\n"
        "Copie config.example.py para config.py e edite com a sua estrutura\n"
        "de pastas/tags antes de rodar o script:\n\n"
        "    cp config.example.py config.py\n",
        file=sys.stderr,
    )
    sys.exit(1)

# ----------------------------------------------------------------------
# Configuração (o resto fica em config.py, que não é versionado)
# ----------------------------------------------------------------------

REMOVED_DIR = os.path.join(VAULT_APPLE_NOTES_DIR, "_Removidos-do-AppleNotes")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sync_state.json")
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")

MAX_FILENAME_LEN = 80

# ----------------------------------------------------------------------
# AppleScript helpers
# ----------------------------------------------------------------------

APPLESCRIPT_FOLDER_DUMP = '''
on replaceText(theText, searchString, replacementString)
	set AppleScript's text item delimiters to searchString
	set theItems to text items of theText
	set AppleScript's text item delimiters to replacementString
	set theText to theItems as string
	set AppleScript's text item delimiters to ""
	return theText
end replaceText

set folderName to "{folder}"
set outLines to {{}}

tell application "Notes"
	set acc to account "{account}"
	set fld to folder folderName of acc
	set noteList to notes of fld
	set totalNotes to count of noteList

	repeat with i from 1 to totalNotes
		set n to item i of noteList
		set noteName to name of n
		set noteBody to plaintext of n
		set noteId to (id of n) as string
		set idSuffix to my replaceText(noteId, "x-coredata://D0091F37-DEF4-407B-99F1-184909AC9F40/ICNote/p", "")
		set creationStr to (creation date of n) as string
		set modStr to (modification date of n) as string

		set cleanBody to my replaceText(noteBody, ASCII character 30, " ")
		set cleanName to my replaceText(noteName, ASCII character 30, " ")

		set recordStr to idSuffix & (ASCII character 31) & cleanName & (ASCII character 31) & creationStr & (ASCII character 31) & modStr & (ASCII character 31) & cleanBody
		set end of outLines to recordStr
	end repeat
end tell

set AppleScript's text item delimiters to (ASCII character 30)
set finalOutput to outLines as string
set AppleScript's text item delimiters to ""
return finalOutput
'''

RS = "\x1e"  # record separator entre notas
US = "\x1f"  # unit separator entre campos


def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"osascript falhou: {result.stderr.strip()}")
    return result.stdout


def fetch_folder_notes(folder_name):
    """Retorna lista de dicts: id, name, created, modified, body para uma pasta."""
    script = APPLESCRIPT_FOLDER_DUMP.replace("{folder}", folder_name).replace("{account}", ACCOUNT_NAME)
    raw = run_applescript(script)
    notes = []
    if not raw.strip():
        return notes
    for record in raw.split(RS):
        if not record.strip():
            continue
        parts = record.split(US)
        if len(parts) != 5:
            continue
        note_id, name, created, modified, body = parts
        # osascript's stdout adds a trailing newline after the last record's
        # last field -- strip it so it doesn't leak into the note body.
        body = body.rstrip("\n\r") if record == raw.split(RS)[-1] else body
        notes.append({
            "id": note_id,
            "name": name,
            "created": created,
            "modified": modified,
            "body": body,
            "folder": folder_name,
        })
    return notes


def list_tracked_folders():
    script = f'''
tell application "Notes"
	set acc to account "{ACCOUNT_NAME}"
	set out to {{}}
	repeat with fld in folders of acc
		set end of out to (name of fld)
	end repeat
end tell
set AppleScript's text item delimiters to "{RS}"
set finalOutput to out as string
set AppleScript's text item delimiters to ""
return finalOutput
'''
    raw = run_applescript(script)
    # osascript's stdout adds a trailing newline after the last folder name
    # (but real folder names can have meaningful trailing spaces, like
    # "Citações ", so only strip \n/\r, not all whitespace).
    all_folders = [f.rstrip("\n\r") for f in raw.split(RS) if f.strip()]
    return [f for f in all_folders if f not in EXCLUDED_FOLDERS]


# ----------------------------------------------------------------------
# Filesystem helpers
# ----------------------------------------------------------------------

def replace_chars(text, chars, repl="-"):
    for c in chars:
        text = text.replace(c, repl)
    return text


def sanitize_filename(name):
    safe = replace_chars(name, "/:")
    if len(safe) > MAX_FILENAME_LEN:
        safe = safe[:MAX_FILENAME_LEN]
    return safe


def find_existing_file(note_id):
    """Procura em todo o vault um arquivo terminando em ' (<id>).md'."""
    pattern = os.path.join(VAULT_APPLE_NOTES_DIR, "**", f"* ({note_id}).md")
    matches = glob.glob(pattern, recursive=True)
    return matches[0] if matches else None


def read_frontmatter_extra_lines(path):
    """Lê linhas extras do frontmatter (ex: tags:) que não são geradas por este script,
    para preservá-las ao regravar o arquivo."""
    known_prefixes = ("title:", "folder:", "created:", "modified:", "source:")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return []
    frontmatter_lines = parts[1].strip("\n").split("\n")
    extra = [line for line in frontmatter_lines if not line.startswith(known_prefixes)]
    return extra


def write_note_file(path, name, folder, created, modified, body, extra_frontmatter_lines):
    frontmatter = [
        f"title: '{name}'",
        f"folder: {folder}",
        f"created: {created}",
        f"modified: {modified}",
        "source: Apple Notes (iCloud)",
    ] + extra_frontmatter_lines
    content = "---\n" + "\n".join(frontmatter) + "\n---\n\n" + body
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ----------------------------------------------------------------------
# Sync principal
# ----------------------------------------------------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def log(message, log_lines):
    print(message)
    log_lines.append(message)


def main():
    log_lines = []
    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log(f"=== Sync iniciado em {started} ===", log_lines)

    state = load_state()
    seen_ids = set()
    created_count = 0
    updated_count = 0
    unchanged_count = 0
    removed_count = 0
    error_count = 0

    try:
        folders = list_tracked_folders()
    except Exception as e:
        log(f"ERRO ao listar pastas: {e}", log_lines)
        folders = list(FOLDER_DEFAULT_TAGS.keys())

    for folder in folders:
        try:
            notes = fetch_folder_notes(folder)
        except Exception as e:
            log(f"ERRO na pasta '{folder}': {e}", log_lines)
            error_count += 1
            continue

        for note in notes:
            note_id = note["id"]
            seen_ids.add(note_id)

            last_modified = state.get(note_id)
            if last_modified == note["modified"]:
                unchanged_count += 1
                continue

            existing_path = find_existing_file(note_id)
            extra_lines = read_frontmatter_extra_lines(existing_path) if existing_path else []

            if not extra_lines:
                default_tag = FOLDER_DEFAULT_TAGS.get(folder, "diversos")
                extra_lines = [f"tags: [{default_tag}]"]

            safe_name = sanitize_filename(note["name"])
            new_path = os.path.join(VAULT_APPLE_NOTES_DIR, folder, f"{safe_name} ({note_id}).md")

            if existing_path and existing_path != new_path:
                os.remove(existing_path)

            write_note_file(new_path, note["name"], folder, note["created"], note["modified"], note["body"], extra_lines)
            state[note_id] = note["modified"]

            if existing_path:
                updated_count += 1
                log(f"Atualizada: {note['name']} ({note_id})", log_lines)
            else:
                created_count += 1
                log(f"Nova nota: {note['name']} ({note_id}) -> tag padrão aplicada", log_lines)

    # Notas que sumiram do Notes.app (apagadas ou movidas pra fora das pastas
    # acompanhadas): mover para _Removidos-do-AppleNotes em vez de apagar.
    known_ids = set(state.keys())
    gone_ids = known_ids - seen_ids
    for gone_id in gone_ids:
        existing_path = find_existing_file(gone_id)
        if existing_path:
            os.makedirs(REMOVED_DIR, exist_ok=True)
            dest = os.path.join(REMOVED_DIR, os.path.basename(existing_path))
            os.rename(existing_path, dest)
            removed_count += 1
            log(f"Removida do Notes.app, movida para _Removidos-do-AppleNotes: {os.path.basename(existing_path)}", log_lines)
        del state[gone_id]

    save_state(state)

    summary = (f"Resumo: {created_count} criadas, {updated_count} atualizadas, "
               f"{unchanged_count} sem mudança, {removed_count} removidas, {error_count} erros de pasta")
    log(summary, log_lines)

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"sync_{datetime.now().strftime('%Y-%m')}.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n\n")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
