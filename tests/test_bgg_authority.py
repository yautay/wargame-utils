import json
from datetime import date, timedelta

import pytest

from wgu.bgg_authority import AuthorityRegistry


def entry(role='designer'):
    today = date.today()
    return dict(game_id=21551, username='verified-account', role=role,
                reviewed_by='Reviewer', reviewed_on=today.isoformat(),
                expires_on=(today + timedelta(days=30)).isoformat(),
                valid_from='2000-01-01', valid_until='2099-01-01',
                evidence=[dict(url='https://publisher.example/identity',
                               description='Confirms this BGG account and role for this game.')])


def registry(tmp_path, entries):
    path = tmp_path / 'authority.json'
    path.write_text(json.dumps(dict(version=1, entries=entries)), encoding='utf-8')
    return AuthorityRegistry(path)


@pytest.mark.parametrize('role', ['designer', 'publisher_representative', 'community_member'])
def test_verified_role_is_not_automatically_official(tmp_path, role):
    result = registry(tmp_path, [entry(role)]).verify(21551, 'verified-account', 42, '2026-08-01T08:00:00Z')
    assert result['status'] == 'verified'
    assert result['role'] == role
    assert result['clarification_status'] != 'official_clarification'
    assert result['evidence']


def test_official_requires_article_evidence(tmp_path):
    record = entry()
    record['official_posts'] = [dict(article_id=42, evidence=record['evidence'])]
    reg = registry(tmp_path, [record])
    assert reg.verify(21551, 'verified-account', 42, '2026-08-01')['clarification_status'] == 'official_clarification'
    assert reg.verify(21551, 'verified-account', 43, '2026-08-01')['clarification_status'] == 'verified_role_statement'
    assert reg.verify(1444, 'verified-account', 42, '2026-08-01')['status'] == 'unverified'
    assert reg.verify(21551, 'Verified-account', 42, '2026-08-01')['status'] == 'unverified'


def test_unknown_not_classified_as_player(tmp_path):
    result = registry(tmp_path, [entry()]).verify(21551, 'Designer', 42, '2026-08-01')
    assert result['status'] == 'unverified'
    assert result['role'] is None


def test_expired_conflicting_and_outside_role_dates(tmp_path):
    record = entry()
    record['expires_on'] = record['reviewed_on'] = '2001-01-01'
    assert registry(tmp_path, [record]).verify(21551, 'verified-account', 42, '2026-08-01')['status'] == 'unverified'
    assert registry(tmp_path, [entry(), entry('publisher_representative')]).verify(21551, 'verified-account', 42, '2026-08-01')['status'] == 'unverified'
    assert registry(tmp_path, [entry()]).verify(21551, 'verified-account', 42, '1999-01-01')['status'] == 'unverified'
    assert registry(tmp_path, [entry()]).verify(21551, 'verified-account', 42, None)['status'] == 'unverified'


def test_invalid_registry_fails_closed(tmp_path):
    record = entry()
    record['evidence'] = []
    reg = registry(tmp_path, [record])
    assert reg.status == 'invalid'
    assert reg.verify(21551, 'verified-account', 42, '2026-08-01')['status'] == 'unverified'


def test_annotation_keeps_source_intact(tmp_path):
    reg = registry(tmp_path, [entry()])
    post = dict(body='Original', metadata=dict(id='42', username='verified-account', postdate='2026-08-01'), url='https://boardgamegeek.com/article/42')
    reg.annotate([post], 21551)
    assert post['body'] == 'Original'
    assert post['authority'] == 'designer'
    assert post['authority_verification']['game_id'] == 21551


def test_search_automatically_verifies_matching_posts(tmp_path, monkeypatch):
    from wgu.bgg import BGGClient
    registry(tmp_path, [entry()])
    monkeypatch.setenv('BGG_AUTHORITY_FILE', str(tmp_path / 'authority.json'))
    client = BGGClient(tmp_path / 'cache')
    monkeypatch.setattr(client, 'forums', lambda game: [{'id': '2'}])
    monkeypatch.setattr(client, 'threads', lambda forum, page: [{'id': '3', 'subject': 'Question'}])
    monkeypatch.setattr(client, 'thread', lambda *args, **kwargs: {
        'posts': [dict(body='retreat', metadata=dict(id='42', username='verified-account', postdate='2026-08-01'))],
        'possibly_more': False})
    post = client.search_posts(21551, 'retreat', 2)['matches'][0]['post']
    assert post['authority'] == 'designer'
    assert post['authority_verification']['clarification_status'] == 'verified_role_statement'


def test_thread_with_game_context_verifies(tmp_path, monkeypatch):
    from wgu.bgg import BGGClient
    from defusedxml import ElementTree as ET
    registry(tmp_path, [entry('publisher_representative')])
    monkeypatch.setenv('BGG_AUTHORITY_FILE', str(tmp_path / 'authority.json'))
    client = BGGClient(tmp_path / 'cache')
    monkeypatch.setattr(client, 'xml', lambda *args, **kwargs: ET.fromstring(
        '<thread><articles><article id="42" username="verified-account" postdate="2026-08-01"><body>Original</body></article></articles></thread>'))
    post = client.thread(3, game_id=21551)['posts'][0]
    assert post['authority'] == 'publisher_representative'
    assert post['body'] == 'Original'
