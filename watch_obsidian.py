#!/usr/bin/env python3
"""
watch_obsidian.py

Roda a cada ~15s via launchd (veja agendamento/macos/com.pedro.obsidianlaunchsync.plist).
Detecta a transição de "Obsidian fechado" -> "Obsidian aberto" e dispara o
notes_sync.py uma única vez por sessão (não fica rodando sync repetido
enquanto o Obsidian continua aberto).

Zero dependências externas -- só biblioteca padrão do Python.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, ".obsidian_watch_state")
SYNC_SCRIPT = os.path.join(HERE, "notes_sync.py")

# Nome do processo como aparece no Activity Monitor / `ps aux`. Se o
# watcher nunca disparar, confirme o nome exato com:
#   ps aux | grep -i obsidian
OBSIDIAN_PROCESS_NAME = "Obsidian"


def obsidian_running():
    result = subprocess.run(["pgrep", "-x", OBSIDIAN_PROCESS_NAME], capture_output=True, text=True)
    return result.returncode == 0


def main():
    was_running = os.path.exists(STATE_FILE)
    now_running = obsidian_running()

    if now_running and not was_running:
        # Obsidian acabou de abrir nesta janela de checagem -- dispara o sync.
        subprocess.run([sys.executable, SYNC_SCRIPT])

    if now_running:
        open(STATE_FILE, "w").close()
    elif was_running:
        os.remove(STATE_FILE)


if __name__ == "__main__":
    main()
