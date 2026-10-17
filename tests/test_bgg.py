import io

import pytest

from wgu.bgg import BGGClient, BGGError, positive, NoRedirect


class Response(io.BytesIO):
    status = 200


class Opener:
    def __init__(self, xml):
        self.data = xml
        self.calls = []

    def open(self, req, timeout):
        self.calls.append(req)
        return Response(self.data)


def test_cache_auth_and_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setenv('BGG_API_TOKEN', 'test-secret')
    opener = Opener(b'<forums><forum id="2" name="Rules"/></forums>')
    sleeps = []
    client = BGGClient(tmp_path, opener=opener, sleep=sleeps.append, clock=lambda: 10)
    assert client.forums(1)[0]['name'] == 'Rules'
    client.forums(1)
    assert len(opener.calls) == 1
    assert opener.calls[0].get_header('Authorization') == 'Bearer test-secret'
    client.forums(3)
    assert sleeps == [5]
    assert all('test-secret' not in p.name and b'test-secret' not in p.read_bytes()
               for p in tmp_path.iterdir())


def test_missing_token(tmp_path, monkeypatch):
    monkeypatch.delenv('BGG_API_TOKEN', raising=False)
    with pytest.raises(BGGError, match='BGG_API_TOKEN'):
        BGGClient(tmp_path).forums(1)


def test_original_posts_and_continuation(tmp_path, monkeypatch):
    monkeypatch.setenv('BGG_API_TOKEN', 'test-secret')
    client = BGGClient(tmp_path, opener=Opener(b'<thread><articles><article id="42" username="player" postdate="2026-10-17"><subject>Rule</subject><body>A &amp; B &lt;b&gt;original&lt;/b&gt;</body></article></articles></thread>'))
    result = client.thread(5, count=1)
    assert result['posts'][0]['body'] == 'A & B <b>original</b>'
    assert result['posts'][0]['authority'] == 'unverified'
    assert result['posts'][0]['url'].endswith('/article/42')
    assert result['next_min_article_id'] == 43
    assert result['possibly_more']


def test_search_scope_and_game_membership(tmp_path, monkeypatch):
    client = BGGClient(tmp_path)
    monkeypatch.setattr(client, 'forums', lambda game: [{'id': '2'}])
    monkeypatch.setattr(client, 'threads', lambda forum, page: [{'subject': 'Retreat rule', 'id': '3'}])
    result = client.find_clarifications(1, 'retreat', 2)
    assert len(result['matches']) == 1
    assert result['threads_scanned'] == 1
    with pytest.raises(ValueError):
        client.find_clarifications(1, 'retreat', 9)


def test_validation_and_no_redirect():
    for value in (0, -1, True, '1'):
        with pytest.raises(ValueError):
            positive(value)
    assert NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.test') is None


def test_mcp_tools():
    from wgu.bgg_mcp import create_server
    import asyncio
    server = create_server()
    names = {tool.name for tool in asyncio.run(server.list_tools())}
    assert names == {'bgg_search_games', 'bgg_forums', 'bgg_find_clarifications', 'bgg_threads', 'bgg_thread', 'bgg_search_posts', 'bgg_verify_authority'}


def post_search_client(tmp_path, monkeypatch, threads):
    client = BGGClient(tmp_path)
    monkeypatch.setattr(client, 'forums', lambda game: [{'id': '2'}])
    monkeypatch.setattr(client, 'threads', lambda forum, page: threads)
    return client


def batch(body, article_id=10, more=False):
    return {'posts': [{'body': body, 'metadata': {'id': str(article_id), 'username': 'player'},
                       'url': f'https://boardgamegeek.com/article/{article_id}', 'authority': 'unverified'}],
            'possibly_more': more, 'next_min_article_id': article_id + 1}


def test_body_match_without_title_and_original_preserved(tmp_path, monkeypatch):
    client = post_search_client(tmp_path, monkeypatch, [{'id': '3', 'subject': 'Question'}])
    original = '<p>RETREAT <b>movement</b> &amp;\n combat</p>'
    monkeypatch.setattr(client, 'thread', lambda *args, **kwargs: batch(original))
    result = client.search_posts(1, 'retreat movement & combat', 2)
    assert result['matches'][0]['post']['body'] == original
    assert result['matches'][0]['post']['metadata']['username'] == 'player'
    assert result['posts_scanned'] == 1
    assert result['next_cursor'] is None


def test_budget_and_resume_within_thread(tmp_path, monkeypatch):
    client = post_search_client(tmp_path, monkeypatch, [{'id': '3'}, {'id': '4'}])
    calls = []
    def fetch(thread_id, count, min_article_id):
        calls.append((thread_id, min_article_id))
        return batch('retreat', 10, True) if min_article_id == 1 else batch('unrelated', 11)
    monkeypatch.setattr(client, 'thread', fetch)
    first = client.search_posts(1, 'retreat', 2, max_batches=1)
    assert first['next_cursor'] == {'page': 1, 'thread_offset': 0, 'min_article_id': 11}
    second = client.search_posts(1, 'retreat', 2, max_batches=1, **first['next_cursor'])
    assert calls == [(3, 1), (3, 11)]
    assert second['matches'] == []
    assert second['next_cursor']['thread_offset'] == 1


def test_page_end_and_next_page(tmp_path, monkeypatch):
    client = post_search_client(tmp_path, monkeypatch, [{'id': str(n)} for n in range(1, 51)])
    monkeypatch.setattr(client, 'thread', lambda *args, **kwargs: batch('nothing'))
    result = client.search_posts(1, 'retreat', 2, thread_offset=49)
    assert result['next_cursor'] == {'page': 2, 'thread_offset': 0, 'min_article_id': 1}
    assert result['batches_scanned'] == 1


def test_body_search_stops_on_error_with_partial_results(tmp_path, monkeypatch):
    client = post_search_client(tmp_path, monkeypatch, [{'id': '3'}, {'id': '4'}])
    def fetch(thread_id, **kwargs):
        if thread_id == 4:
            raise BGGError('BGG HTTP 429; zapytanie zatrzymane.')
        return batch('retreat')
    monkeypatch.setattr(client, 'thread', fetch)
    result = client.search_posts(1, 'retreat', 2)
    assert len(result['matches']) == 1
    assert result['stop_reason'] == 'bgg_error'
    assert result['next_cursor']['thread_offset'] == 1


@pytest.mark.parametrize('kwargs', [{'max_batches': 6}, {'thread_offset': -1}, {'page': 0},
                                    {'min_article_id': 0}, {'query': ' '}])
def test_body_search_validates_before_network(tmp_path, monkeypatch, kwargs):
    client = BGGClient(tmp_path)
    def unexpected(*args, **kwargs):
        pytest.fail('network before validation')
    monkeypatch.setattr(client, 'forums', unexpected)
    params = dict(game_id=1, query='retreat', forum_id=2)
    params.update(kwargs)
    with pytest.raises(ValueError):
        client.search_posts(**params)


def test_body_search_cache_and_throttle(tmp_path, monkeypatch):
    from urllib.parse import urlparse
    monkeypatch.setenv('BGG_API_TOKEN', 'test-secret')
    opener = Opener(b'')
    def fetch(req, timeout):
        opener.calls.append(req)
        endpoint = urlparse(req.full_url).path.rsplit('/', 1)[-1]
        return Response({'forumlist': b'<forums><forum id="2"/></forums>',
                         'forum': b'<forum><threads><thread id="3" subject="Question"/></threads></forum>',
                         'thread': b'<thread><articles><article id="10"><body>Retreat!</body></article></articles></thread>'}[endpoint])
    monkeypatch.setattr(opener, 'open', fetch)
    sleeps = []
    client = BGGClient(tmp_path, opener=opener, sleep=sleeps.append, clock=lambda: 0)
    assert len(client.search_posts(1, 'retreat', 2)['matches']) == 1
    client.search_posts(1, 'retreat', 2)
    assert len(opener.calls) == 3
    assert sleeps == [5, 5]


def test_http_retry_and_auth_failure(tmp_path, monkeypatch):
    from urllib.error import HTTPError
    monkeypatch.setenv('BGG_API_TOKEN', 'test-secret')
    opener = Opener(b'<forums/>')
    original = opener.open
    attempts = []

    def flaky(req, timeout):
        attempts.append(1)
        if len(attempts) == 1:
            raise HTTPError(req.full_url, 429, '', {'Retry-After': '12'}, None)
        return original(req, timeout)

    monkeypatch.setattr(opener, 'open', flaky)
    sleeps = []
    client = BGGClient(tmp_path, opener=opener, sleep=sleeps.append, clock=lambda: 0)
    assert client.forums(1) == []
    assert 12 in sleeps

    def denied(req, timeout):
        raise HTTPError(req.full_url, 401, '', {}, None)

    monkeypatch.setattr(opener, 'open', denied)
    with pytest.raises(BGGError, match='401'):
        client.forums(2)


def test_unsafe_xml_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv('BGG_API_TOKEN', 'test-secret')
    client = BGGClient(tmp_path, opener=Opener(b'<!DOCTYPE x [<!ENTITY e "bad">]><forums>&e;</forums>'))
    with pytest.raises(BGGError, match='XML'):
        client.forums(1)
    assert not list(tmp_path.glob('*.xml'))
