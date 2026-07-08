# Template de configuração. Copie este arquivo para config.py e edite os
# valores abaixo com a sua própria estrutura de pastas/tags:
#
#     cp config.example.py config.py
#
# config.py não é versionado (está no .gitignore) -- é onde ficam os
# detalhes pessoais (nomes de pasta, taxonomia de tags), mantendo o
# restante do código público e reutilizável.

import os

# Pasta dentro do seu vault do Obsidian onde as notas exportadas do
# Notes.app vivem.
VAULT_APPLE_NOTES_DIR = os.path.expanduser("~/Documents/Obsidian Vault/Apple Notes")

# Nome da conta no Notes.app (visível na barra lateral do app: iCloud,
# Gmail, On My Mac, etc.)
ACCOUNT_NAME = "iCloud"

# Pastas do Notes.app que o sync deve ignorar (ex: uma pasta de senhas,
# ou a lixeira).
EXCLUDED_FOLDERS = {"Passwords", "Recently Deleted"}

# Tag padrão aplicada a notas NOVAS que aparecerem em cada pasta. Notas
# que já existem no vault mantêm a tag que você já atribuiu a elas --
# isso só vale para notas criadas depois da primeira exportação.
FOLDER_DEFAULT_TAGS = {
    "Folder1": "tag1",
    "Folder2": "tag2",
    "Catch-all Folder": "misc",
}
