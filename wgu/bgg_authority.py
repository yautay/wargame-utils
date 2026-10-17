"""Evidence reviewed by the operator, never inferred from names or post contents."""
from datetime import date
import json
import os
from pathlib import Path
from urllib.parse import urlparse


def _sources(value):
    if not isinstance(value, list) or not value:
        raise ValueError("Brak źródeł weryfikacji.")
    for source in value:
        if not isinstance(source, dict) or not isinstance(source.get('description'), str) or not source['description'].strip():
            raise ValueError("Źródło wymaga opisu dowodu.")
        url = urlparse(source.get('url', ''))
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError("Źródło wymaga publicznego adresu HTTPS.")


class AuthorityRegistry:
    def __init__(self, path=None):
        self.entries = []
        self.status = 'not_configured'
        path = path or os.environ.get('BGG_AUTHORITY_FILE')
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            if data['version'] != 1 or not isinstance(data['entries'], list):
                raise ValueError("Nieprawidłowy format rejestru.")
            for entry in data['entries']:
                if not isinstance(entry, dict) or not isinstance(entry.get('official_posts', []), list):
                    raise ValueError("Nieprawidłowy rekord.")
                if type(entry['game_id']) is not int or entry['game_id'] <= 0:
                    raise ValueError("Nieprawidłowy identyfikator gry.")
                if not isinstance(entry['username'], str) or not entry['username'].strip():
                    raise ValueError("Brak konta BGG.")
                if entry['role'] not in {'designer', 'publisher_representative', 'community_member'}:
                    raise ValueError("Nieprawidłowa rola.")
                if not isinstance(entry['reviewed_by'], str) or not entry['reviewed_by'].strip():
                    raise ValueError("Brak osoby weryfikującej.")
                reviewed = date.fromisoformat(entry['reviewed_on'])
                expires = date.fromisoformat(entry['expires_on'])
                if reviewed > date.today() or expires < reviewed:
                    raise ValueError("Nieprawidłowa data przeglądu.")
                start = date.fromisoformat(entry['valid_from'])
                end = date.fromisoformat(entry['valid_until'])
                if end < start:
                    raise ValueError("Nieprawidłowy okres pełnienia roli.")
                _sources(entry['evidence'])
                for ruling in entry.get('official_posts', []):
                    if not isinstance(ruling, dict):
                        raise ValueError("Nieprawidłowy dowód klaryfikacji.")
                    if type(ruling['article_id']) is not int or ruling['article_id'] <= 0:
                        raise ValueError("Nieprawidłowy identyfikator wpisu.")
                    _sources(ruling['evidence'])
            self.entries = data['entries']
            self.status = 'loaded'
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self.status = 'invalid'  # Fail closed; never expose file content or paths.

    def verify(self, game_id, username, article_id=None, postdate=None):
        result = {'game_id': game_id, 'username': username, 'status': 'unverified',
                  'role': None, 'clarification_status': 'unverified', 'evidence': [],
                  'registry_status': self.status,
                  'method': 'operator_reviewed_evidence',
                  'reason': 'Brak aktualnego dowodu powiązania konta z tą grą; nie oznacza to, że autor jest graczem.'}
        if self.status != 'loaded':
            return result
        candidates = [e for e in self.entries if e['game_id'] == game_id and e['username'] == username
                      and date.fromisoformat(e['expires_on']) >= date.today()]
        try:
            posted = date.fromisoformat(postdate[:10]) if postdate else None
        except (ValueError, TypeError):
            posted = None
        if posted is None:
            result['reason'] = 'Brak poprawnej daty wpisu; nie można sprawdzić okresu pełnienia roli.'
            return result
        candidates = [e for e in candidates if date.fromisoformat(e['valid_from']) <= posted <= date.fromisoformat(e['valid_until'])]
        if len(candidates) != 1:
            if len(candidates) > 1:
                result['reason'] = 'Niejednoznaczne powiązanie w rejestrze; wymagany przegląd.'
            return result
        entry = candidates[0]
        result.update(status='verified', role=entry['role'], evidence=entry['evidence'],
                      reviewed_by=entry['reviewed_by'], reviewed_on=entry['reviewed_on'],
                      expires_on=entry['expires_on'],
                      clarification_status=('community_interpretation' if entry['role'] == 'community_member'
                                            else 'verified_role_statement'),
                      reason='Rola potwierdzona w lokalnym rejestrze dowodów; treść wpisu wymaga oceny.')
        rulings = [r for r in entry.get('official_posts', []) if r['article_id'] == article_id]
        if len(rulings) == 1 and entry['role'] in {'designer', 'publisher_representative'}:
            result.update(clarification_status='official_clarification', official_evidence=rulings[0]['evidence'])
        return result

    def annotate(self, posts, game_id):
        for post in posts:
            metadata = post['metadata']
            verification = self.verify(game_id, metadata.get('username'), int(metadata['id']), metadata.get('postdate'))
            post['authority_verification'] = verification
            post['authority'] = verification['role'] if verification['status'] == 'verified' else 'unverified'
