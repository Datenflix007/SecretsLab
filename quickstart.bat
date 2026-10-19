@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo === Secrets Lab Quickstart (Windows) ===
where docker >nul 2>&1 || (echo FEHLER: Docker nicht gefunden. & exit /b 1)
docker info >nul 2>&1 || (echo FEHLER: Docker Desktop starten. & exit /b 1)
docker compose up -d || exit /b 1
set "VAULT_ARGS=-e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token"
set /a RETRIES=0
:waitvault
docker exec %VAULT_ARGS% secrets-lab-vault vault status >nul 2>&1
if not errorlevel 1 goto vaultready
set /a RETRIES+=1
if %RETRIES% GEQ 30 (echo FEHLER: Vault wurde nicht bereit. & exit /b 1)
timeout /t 2 /nobreak >nul
goto waitvault
:vaultready
docker exec %VAULT_ARGS% secrets-lab-vault vault read transit/keys/user-secrets >nul 2>&1
if errorlevel 1 (
  docker exec %VAULT_ARGS% secrets-lab-vault vault secrets enable transit >nul 2>&1
  docker exec %VAULT_ARGS% secrets-lab-vault vault write -f transit/keys/user-secrets || exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 -m venv .venv || exit /b 1
  ) else (
    python -m venv .venv || exit /b 1
  )
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
cls
echo === Testumgebung bereit ===
echo Nur fiktive API-Keys benutzen!
".venv\Scripts\python.exe" menu.py
endlocal
