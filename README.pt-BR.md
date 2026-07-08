# apple-notes-obsidian-sync

Sincronização em um sentido só (Apple Notes -> Obsidian) para o conjunto
de pastas do Notes.app que foi exportado pro vault do Obsidian. Se você
editar uma nota direto no Notes.app (Mac ou iPhone, via iCloud), esse
script atualiza o `.md` correspondente no vault na próxima execução. Ele
**não** escreve de volta no Notes.app — edições feitas só no Obsidian
(como o campo `tags:`) não são tocadas por esse script e não são
enviadas ao Notes.app.

Zero dependências externas — só biblioteca padrão do Python 3.8+.

## Como funciona

1. Lê todas as notas de um conjunto fixo de pastas do Notes.app (pula
   `Senhas` e `Recently Deleted` de propósito) via AppleScript (`osascript`).
2. Casa cada nota com o `.md` correspondente no vault usando o ID interno
   da nota no Apple Notes, embutido no nome do arquivo como `Título (id).md`.
3. Se a nota mudou (data de modificação diferente) ou é nova, reescreve o
   corpo do `.md`, o `created`/`modified` do frontmatter, e renomeia o
   arquivo se o título mudou — preservando qualquer linha extra de
   frontmatter que você tenha adicionado (tipo `tags:`).
4. Se uma nota antes acompanhada sumir do Notes.app (apagada ou movida
   pra fora de uma pasta acompanhada), o arquivo é movido pra
   `_Removidos-do-AppleNotes/` dentro do vault em vez de ser apagado.
5. Grava um resumo em `Logs/sync_AAAA-MM.log` a cada execução.

## Requisitos

- macOS com o Notes.app logado na mesma conta iCloud das notas que você
  quer sincronizar
- Python 3.8+ (já vem no macOS)
- O vault do Obsidian já precisa ter a estrutura de pastas `Apple Notes/`
  que esse script espera (a mesma da exportação feita em julho/2026)

## Configuração

Os dados pessoais (caminho do vault, nome da conta no Notes.app, nomes
de pasta e a sua taxonomia de tags) ficam em `config.py`, que está no
`.gitignore` e nunca é commitado — é isso que mantém a estrutura de
pastas/tags privada enquanto a lógica do sync continua pública.

```bash
cp config.example.py config.py
```

Depois edite o `config.py`:

| Variável                 | O que é                                              |
|---------------------------|-------------------------------------------------------|
| `VAULT_APPLE_NOTES_DIR`    | Caminho da pasta `Apple Notes/` dentro do seu vault    |
| `ACCOUNT_NAME`             | Nome da conta no Notes.app (barra lateral do app)      |
| `EXCLUDED_FOLDERS`         | Pastas a ignorar (ex: pasta de senhas, lixeira)        |
| `FOLDER_DEFAULT_TAGS`      | Tag aplicada a notas novas, por pasta                  |

O `notes_sync.py` em si não tem nenhum dado pessoal — pode ficar público sem problema.

## Uso rápido

```bash
git clone https://github.com/pedrosimoess/apple-notes-obsidian-sync.git
cd apple-notes-obsidian-sync
cp config.example.py config.py   # depois edite o config.py
python3 notes_sync.py
```

Na primeira execução o macOS vai pedir permissão pro Terminal/Python
controlar o Notes.app (Ajustes do Sistema → Privacidade e Segurança →
Automação).

## Agendamento (macOS / launchd)

Veja `agendamento/macos/LEIAME.md` pra instalar os `.plist` incluídos:
um roda o sync a cada 30 minutos, o outro (`watch_obsidian.py`) checa a
cada 15s e dispara o sync assim que detecta que o Obsidian.app acabou
de ser aberto.

## Observações

- A tag de uma nota nunca é atribuída automaticamente pra notas
  existentes — esse script só preserva o que já tiver em `tags:` no
  arquivo. Notas novas recebem uma tag padrão conforme a pasta do
  Notes.app onde estão (veja `FOLDER_DEFAULT_TAGS`); a pasta genérica
  "Notes" usa `diversos` como padrão pra notas novas, já que a
  classificação por conteúdo foi feita manualmente e não é replicada aqui.
- O estado (última data de modificação vista por nota) fica em
  `.sync_state.json`, fora do git — apague esse arquivo pra forçar uma
  reescaneada completa.
