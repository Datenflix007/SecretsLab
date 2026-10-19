"""Minimal interactive launcher for the local development lab."""
import subprocess
import sys


def run(*args):
    subprocess.run([sys.executable, 'lab.py', *args], check=False)


def main():
    user = input('Testnutzer [alice]: ').strip() or 'alice'
    provider = input('Provider [openai]: ').strip() or 'openai'
    while True:
        print('\n[1] Key speichern  [2] Metadaten  [3] Key entschlüsseln  [4] Löschen  [5] MongoDB ansehen  [0] Beenden')
        action = input('Auswahl: ').strip()
        if action == '0':
            break
        if action == '1':
            run('put', '--user', user, '--provider', provider)
        elif action == '2':
            run('list', '--user', user)
        elif action == '3':
            run('get', '--user', user, '--provider', provider)
        elif action == '4':
            run('delete', '--user', user, '--provider', provider)
        elif action == '5':
            subprocess.run(['docker', 'exec', 'secrets-lab-mongo', 'mongosh', '--quiet', '--eval', "db.getSiblingDB('secrets_lab').user_secrets.find().pretty()"], check=False)
        else:
            print('Unbekannte Auswahl.')


if __name__ == '__main__':
    main()
