"""Minimal interactive launcher for the local development lab."""
import subprocess
import sys

PROVIDERS = ('openai', 'anthropic', 'google', 'mistral', 'cohere')


def run(*args):
    subprocess.run([sys.executable, 'lab.py', *args], check=False)


def saved_providers(user):
    """Return the providers that already have a key for this test user."""
    result = subprocess.run(
        [sys.executable, 'lab.py', 'list', '--user', user, '--providers-only'],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def choose_provider(providers, prompt):
    if not providers:
        print('Keine passenden Provider vorhanden.')
        return None
    print('\n' + '  '.join(f'[{index}] {provider}' for index, provider in enumerate(providers, 1)))
    choice = input(prompt).strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(providers):
        print('Ungültige Auswahl.')
        return None
    return providers[int(choice) - 1]


def main():
    user = input('Testnutzer [alice]: ').strip() or 'alice'
    while True:
        print('\n[1] Key speichern  [2] Metadaten  [3] Key entschlüsseln  [4] Löschen  [5] MongoDB ansehen  [0] Beenden')
        action = input('Auswahl: ').strip()
        if action == '0':
            break
        if action == '1':
            used = saved_providers(user)
            provider = choose_provider(
                [provider for provider in PROVIDERS if provider not in used],
                'Provider für neuen Key: ',
            )
            if provider:
                run('put', '--user', user, '--provider', provider)
        elif action == '2':
            run('list', '--user', user)
        elif action == '3':
            provider = choose_provider(saved_providers(user), 'Provider zum Entschlüsseln: ')
            if provider:
                run('get', '--user', user, '--provider', provider)
        elif action == '4':
            provider = choose_provider(saved_providers(user), 'Provider zum Löschen: ')
            if provider:
                run('delete', '--user', user, '--provider', provider)
        elif action == '5':
            subprocess.run(['docker', 'exec', 'secrets-lab-mongo', 'mongosh', '--quiet', '--eval', "db.getSiblingDB('secrets_lab').user_secrets.find().pretty()"], check=False)
        else:
            print('Unbekannte Auswahl.')


if __name__ == '__main__':
    main()
