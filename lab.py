"""Local-only envelope-encryption lab. Not a production secrets service."""
import argparse
import base64
import os
import sys
from datetime import datetime, timezone

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pymongo import MongoClient

VAULT_URL = os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200')
VAULT_TOKEN = os.getenv('VAULT_TOKEN', 'dev-only-token')
MONGO_URL = os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27018/')
KEY_NAME = 'user-secrets'


def vault(path, payload):
    r = requests.post(
        f'{VAULT_URL}/v1/{path}',
        json=payload,
        headers={'X-Vault-Token': VAULT_TOKEN},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()['data']


def b64(data):
    return base64.b64encode(data).decode('ascii')


def aad(user, provider):
    return f'user-secrets:v1:{user}:{provider}'.encode()


def main():
    parser = argparse.ArgumentParser(description='Local vault + MongoDB secrets test')
    parser.add_argument('operation', choices=['put', 'list', 'get', 'delete'])
    parser.add_argument('--user', default='demo-user')
    parser.add_argument('--provider', default='openai')
    args = parser.parse_args()

    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    coll = client['secrets_lab']['user_secrets']
    coll.create_index([('user_id', 1), ('provider', 1)], unique=True)
    selector = {'user_id': args.user, 'provider': args.provider}

    if args.operation == 'put':
        from getpass import getpass
        secret = getpass('Fiktiven API-Key eingeben (nicht sichtbar): ')
        if not secret:
            parser.error('Leerer Schlüssel')
        # Vault creates and wraps a fresh 256-bit DEK with its KEK.
        data = vault(f'transit/datakey/plaintext/{KEY_NAME}', {'bits': 256})
        dek = base64.b64decode(data['plaintext'])
        nonce = os.urandom(12)
        # AESGCM produces ciphertext with a 16-byte authentication tag appended.
        ciphertext = AESGCM(dek).encrypt(nonce, secret.encode(), aad(args.user, args.provider))
        doc = {
            **selector,
            'schema_version': 1,
            'encrypted_secret': {'algorithm': 'AES-256-GCM', 'nonce': b64(nonce), 'ciphertext_and_tag': b64(ciphertext)},
            'key_encryption': {'encrypted_dek': data['ciphertext'], 'kek_id': KEY_NAME},
            'metadata': {'last_four': secret[-4:], 'status': 'unverified'},
            'updated_at': datetime.now(timezone.utc),
        }
        coll.replace_one(selector, doc, upsert=True)
        print('Gespeichert. MongoDB enthält keinen unverschlüsselten API-Key.')
    elif args.operation == 'list':
        for doc in coll.find({'user_id': args.user}, {'_id': 0, 'provider': 1, 'metadata': 1}):
            print(doc)
    elif args.operation == 'get':
        doc = coll.find_one(selector)
        if not doc:
            print('Kein Eintrag gefunden.')
            return
        data = vault(f'transit/decrypt/{doc["key_encryption"]["kek_id"]}',
                     {'ciphertext': doc['key_encryption']['encrypted_dek']})
        dek = base64.b64decode(data['plaintext'])
        enc = doc['encrypted_secret']
        secret = AESGCM(dek).decrypt(
            base64.b64decode(enc['nonce']),
            base64.b64decode(enc['ciphertext_and_tag']),
            aad(args.user, args.provider),
        ).decode()
        print('Nur für den lokalen Test entschlüsselt:', secret)
    elif args.operation == 'delete':
        count = coll.delete_one(selector).deleted_count
        print('Gelöscht.' if count else 'Kein Eintrag gefunden.')


if __name__ == '__main__':
    try:
        main()
    except (requests.RequestException, Exception) as exc:
        print(f'Fehler: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)
