# Agendamento no macOS (launchd)

Tem dois `.plist` aqui, independentes -- pode instalar um, o outro, ou os dois:

- `com.pedro.applenotessync.plist`: roda o `notes_sync.py` a cada 30
  minutos (`StartInterval = 1800`), não importa se o Obsidian está aberto.
- `com.pedro.obsidianlaunchsync.plist`: roda o `watch_obsidian.py` a
  cada 15 segundos, que só dispara o `notes_sync.py` quando detecta que
  o Obsidian.app acabou de ser aberto (ou seja: sync automático assim
  que você abre o Obsidian, com atraso de até ~15s). Não fica rodando o
  sync de novo enquanto o Obsidian continua aberto.

## Instalar

```bash
mkdir -p ~/Library/LaunchAgents
cp com.pedro.applenotessync.plist ~/Library/LaunchAgents/
cp com.pedro.obsidianlaunchsync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pedro.applenotessync.plist
launchctl load ~/Library/LaunchAgents/com.pedro.obsidianlaunchsync.plist
```

## Verificar se está rodando

```bash
launchctl list | grep pedro
```

## Parar / desinstalar

```bash
launchctl unload ~/Library/LaunchAgents/com.pedro.applenotessync.plist
launchctl unload ~/Library/LaunchAgents/com.pedro.obsidianlaunchsync.plist
rm ~/Library/LaunchAgents/com.pedro.applenotessync.plist
rm ~/Library/LaunchAgents/com.pedro.obsidianlaunchsync.plist
```

## Logs

- Saída normal: `Logs/launchd.out.log` (sync a cada 30min) / `Logs/watch.out.log` (watcher do Obsidian)
- Erros: `Logs/launchd.err.log` / `Logs/watch.err.log`
- Log do próprio script (resumo por execução): `Logs/sync_AAAA-MM.log`

## Se o watcher não disparar

O `watch_obsidian.py` procura um processo chamado exatamente `Obsidian`.
Confirme o nome real com `ps aux | grep -i obsidian` e ajuste a constante
`OBSIDIAN_PROCESS_NAME` no topo do script se for diferente.

## Permissão de automação

Na primeira execução, o macOS vai pedir permissão para o Terminal/Python
controlar o app Notes (Ajustes do Sistema → Privacidade e Segurança →
Automação). Se o launchd falhar silenciosamente na primeira vez, rode o
script manualmente uma vez (`python3 notes_sync.py`) pra conceder a
permissão antes de agendar.

Ajuste o intervalo mudando `StartInterval` (em segundos) e recarregando:

```bash
launchctl unload ~/Library/LaunchAgents/com.pedro.applenotessync.plist
launchctl load ~/Library/LaunchAgents/com.pedro.applenotessync.plist
```
