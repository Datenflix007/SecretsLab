#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo '=== Secrets Lab Quickstart (Linux/macOS) ==='
command -v docker >/dev/null || { echo 'FEHLER: Docker fehlt.' >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo 'FEHLER: Docker-Daemon starten.' >&2; exit 1; }
docker compose up -d
vexec=(docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token secrets-lab-vault vault)
ready=0
for _ in $(seq 1 30); do
  if "${vexec[@]}" status >/dev/null 2>&1; then ready=1; break; fi
  sleep 2
done
[[ "$ready" == 1 ]] || { echo 'FEHLER: Vault wurde nicht bereit.' >&2; exit 1; }
if ! "${vexec[@]}" read transit/keys/user-secrets >/dev/null 2>&1; then
  "${vexec[@]}" secrets enable transit >/dev/null 2>&1 || true
  "${vexec[@]}" write -f transit/keys/user-secrets
fi
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
printf '\n=== Testumgebung bereit ===\nNur fiktive API-Keys verwenden!\n'
.venv/bin/python menu.py
