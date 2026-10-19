# Secrets Lab – lokaler BYOK-Test

Isolierte Testumgebung für **Envelope Encryption** mit HashiCorp Vault Transit, AES-256-GCM und MongoDB. Enthält ein interaktives Terminalmenü.

> **Niemals echte API-Schlüssel verwenden!** Die Umgebung verwendet den unsicheren Vault-Dev-Modus (HTTP, bekanntes Root-Token), eine MongoDB ohne Authentifizierung und zeigt auf Wunsch den API-Key im Klartext. Nur auf dem eigenen Rechner ausführen; nicht öffentlich bereitstellen.

## Quickstart Windows
1. Docker Desktop starten (Linux-Container).
2. Python >=3.11 installieren.
3. Ordner entpacken, `quickstart.bat` per Doppelklick oder über PowerShell starten.
4. Menü verwenden: Key eingeben (nur Fantasiewerte), Metadaten ansehen, entschlüsseln und löschen.

## Quickstart Linux/macOS
Voraussetzungen: Docker mit Compose-Plugin, Python >=3.11 inklusive `venv`.

```bash
chmod +x quickstart.sh
./quickstart.sh
```

Das Skript startet MongoDB (`127.0.0.1:27018`) und Vault (`127.0.0.1:8200`), wartet auf Vault, aktiviert bei Bedarf Transit, erstellt den `user-secrets`-Schlüssel, installiert Python-Pakete in `.venv` und öffnet ein Terminalmenü. Vault-CLI-Aufrufe setzen explizit `VAULT_ADDR=http://127.0.0.1:8200`, um den HTTP/HTTPS-Fehler zu verhindern. Wiederholte Starts sind möglich; **nach dem Neustart des Vault-Dev-Containers gehen seine Schlüssel verloren**. Alte MongoDB-Einträge lassen sich dann nicht mehr entschlüsseln.

## Direkte CLI-Befehle

Windows:
```powershell
.\.venv\Scripts\python.exe lab.py put --user alice --provider openai
.\.venv\Scripts\python.exe lab.py list --user alice
.\.venv\Scripts\python.exe lab.py get --user alice --provider openai
.\.venv\Scripts\python.exe lab.py delete --user alice --provider openai
```
Linux/macOS entsprechend `.venv/bin/python`.

MongoDB-Inhalt:
```bash
docker exec secrets-lab-mongo mongosh --quiet --eval "db.getSiblingDB('secrets_lab').user_secrets.find().pretty()"
```

## Datenmodell
In MongoDB `secrets_lab.user_secrets` liegen ausschließlich AES-256-GCM-Ciphertext, Nonce, ein von Vault verschlüsselter DEK sowie Metadaten (`user_id`, `provider`, `last_four`, `status`). Der KEK liegt bei Vault, nicht in MongoDB. `get` entschlüsselt ausdrücklich nur zu Lernzwecken.

## Aufräumen
```bash
docker compose down -v
```
**Achtung:** `-v` löscht die Testdaten in MongoDB. Normales `docker compose down` erhält das MongoDB-Volume, Vault-Dev-Schlüssel gehen aber dennoch verloren. Zum vollständigen Neuanfang: `docker compose down -v` und danach Quickstart neu ausführen.

## Nicht produktionsreif
Keine Nutzeranmeldung, Zugriffstrennung, Provider-Validierung, sicheres Root-Token, TLS, Vault-Persistenz, Audit-Trail oder externe Secrets Policy. Das Python-Programm ist ein lokaler Funktionsnachweis, kein sicherer Mehrbenutzer-Service.
