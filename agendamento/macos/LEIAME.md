# Agendamento no macOS (launchd)

Esse `.plist` roda o `notes_sync.py` a cada 30 minutos (`StartInterval = 1800`
segundos) e também uma vez assim que for carregado (`RunAtLoad`).

## Instalar

```bash
mkdir -p ~/Library/LaunchAgents
cp com.pedro.applenotessync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pedro.applenotessync.plist
```

## Verificar se está rodando

```bash
launchctl list | grep applenotessync
```

## Parar / desinstalar

```bash
launchctl unload ~/Library/LaunchAgents/com.pedro.applenotessync.plist
rm ~/Library/LaunchAgents/com.pedro.applenotessync.plist
```

## Logs

- Saída normal: `Logs/launchd.out.log`
- Erros: `Logs/launchd.err.log`
- Log do próprio script (resumo por execução): `Logs/sync_AAAA-MM.log`

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
