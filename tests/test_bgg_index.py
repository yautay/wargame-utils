"""Integration coverage: one transport, bounded sync, offline FTS and fresh evidence."""
import asyncio
import io
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import date, timedelta
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from xml.sax.saxutils import escape

import pytest

from wgu.bgg import BGGClient, BGGError
from wgu.bgg.index import LocalIndex
from wgu.bgg.service import Bgg


class Response(io.BytesIO):
    status=200


class Api:
    def __init__(self):
        self.calls=[]
        self.fail_thread=None
        self.posts={3:[(i,'Designer' if i==100 else 'someone',
                         'Retreating priorities & <b>rules</b> '+str(i)) for i in range(1,102)],
                    4:[(201,'someone','A stacking question')]}

    def open(self,req,timeout):
        url=urlsplit(req.full_url)
        endpoint=url.path.rsplit('/',1)[-1]
        q={k:v[0] for k,v in parse_qs(url.query).items()}
        self.calls.append((endpoint,q))
        if endpoint=='forumlist':
            body='<forums><forum id="2" title="Rules" numthreads="2"/></forums>'
        elif endpoint=='forum':
            body='<forum><threads>'+''.join(f'<thread id="{t}" subject="Question" lastpostdate="2026-10-17T10:00:00Z"/>' for t in self.posts)+'</threads></forum>'
        elif endpoint=='thread':
            tid=int(q['id'])
            if tid==self.fail_thread:
                raise HTTPError(req.full_url,403,'blocked',{},None)
            rows=[p for p in self.posts[tid] if p[0]>=int(q['minarticleid'])][:int(q['count'])]
            body='<thread><articles>'+''.join(f'<article id="{p}" username="{u}" postdate="2026-08-01T08:00:00-06:00" link="original-link"><subject>Question</subject><body>{escape(b)}</body></article>' for p,u,b in rows)+'</articles></thread>'
        else:
            raise AssertionError('unexpected network request '+endpoint)
        return Response(body.encode())


@pytest.fixture
def world(tmp_path,monkeypatch):
    monkeypatch.setenv('BGG_API_TOKEN','synthetic-secret')
    monkeypatch.delenv('BGG_OFFLINE',raising=False)
    monkeypatch.delenv('WGU_BGG_OFFLINE',raising=False)
    monkeypatch.delenv('BGG_AUTHORITY_FILE',raising=False)
    api=Api()
    sleeps=[]
    client=BGGClient(tmp_path/'xml',opener=api,sleep=sleeps.append,clock=lambda:10)
    project=SimpleNamespace(root=tmp_path,data={'bgg':{'thing_id':1,'authorities':[{'user':'Designer','role':'designer'}]}})
    return api,client,Bgg(project,client),sleeps


def registry(tmp_path,monkeypatch):
    today=date.today()
    entry=dict(game_id=1,username='Designer',role='designer',reviewed_by='Test reviewer',
        reviewed_on=today.isoformat(),expires_on=(today+timedelta(days=30)).isoformat(),
        valid_from='2000-01-01',valid_until='2099-01-01',
        evidence=[{'url':'https://publisher.example/account','description':'Independent account proof'}])
    path=tmp_path/'authority.json'
    path.write_text(json.dumps({'version':1,'entries':[entry]}),encoding='utf-8')
    monkeypatch.setenv('BGG_AUTHORITY_FILE',str(path))
    return path


def test_selected_sync_resumes_without_refetch_and_stays_bounded(world):
    api,client,svc,sleeps=world
    first=svc.sync([3,4],2,max_batches=1)
    assert first['batches_scanned']==1 and first['pending_thread_ids']==[3,4]
    second=svc.sync([3,4],2,max_batches=2)
    assert second['complete'] and second['batches_scanned']==2
    calls=[q for endpoint,q in api.calls if endpoint=='thread']
    assert [(q['id'],q['minarticleid'],q['count']) for q in calls]==[('3','1','100'),('3','101','100'),('4','1','100')]
    before=len(api.calls)
    assert svc.sync([3,4],2,max_batches=2)['batches_scanned']==0
    assert len(api.calls)==before  # XML metadata cache too
    assert all(s>=5 for s in sleeps)


def test_offline_stemming_preserves_source_and_rechecks_authority(world,tmp_path,monkeypatch):
    api,client,svc,_=world
    path=registry(tmp_path,monkeypatch)
    svc.sync([3],2,max_batches=2)
    before=len(api.calls)
    monkeypatch.delenv('BGG_API_TOKEN')
    monkeypatch.setenv('BGG_OFFLINE','1')
    result=client.search_cached_posts(1,'retreat priority',author_role='designer',limit=1)
    post=result['matches'][0]['post']
    assert post['metadata']['id']=='100'
    assert post['metadata']['postdate']=='2026-08-01T08:00:00-06:00'
    assert post['metadata']['link']=='original-link'
    assert post['body']=='Retreating priorities & <b>rules</b> 100'
    assert post['authority_verification']['clarification_status']=='verified_role_statement'
    assert result['network_requests']==0 and len(api.calls)==before
    path.write_text(json.dumps({'version':1,'entries':[]}),encoding='utf-8')
    assert not client.search_cached_posts(1,'retreat',author_role='designer')['matches']
    assert client.search_cached_posts(1,'retreat',author_role='unverified')['matches']
    assert not client.search_cached_posts(9,'retreat')['matches']


def test_legacy_authority_configuration_never_grants_role(world):
    _,client,svc,_=world
    svc.sync([3],2,max_batches=1)
    assert not svc.search_posts('retreat',author_role='designer')['matches']
    with pytest.raises(ValueError): client.search_cached_posts(1,'retreat',author_role='player')


@pytest.mark.parametrize('ids,forum,budget', [([],2,1),([3]*2,2,1),([1,2,3,4,5,6],2,1),([3],2,6),([True],2,1)])
def test_invalid_sync_stops_before_network(world,ids,forum,budget):
    api,_,svc,_=world
    with pytest.raises(ValueError): svc.sync(ids,forum,max_batches=budget)
    assert not api.calls


def test_sync_checks_membership_and_stops_on_error(world):
    api,client,svc,_=world
    with pytest.raises(ValueError): svc.sync([3],99)
    assert [e for e,_ in api.calls]==['forumlist']
    with pytest.raises(ValueError): svc.sync([99],2)
    assert not any(e=='thread' for e,_ in api.calls)
    api.fail_thread=3
    with pytest.raises(BGGError): svc.sync([3,4],2,max_batches=5)
    assert [q['id'] for e,q in api.calls if e=='thread']==['3']
    before=len(api.calls)
    with pytest.raises(BGGError): client.thread(3,game_id=99)
    assert len(api.calls)==before


def test_unknown_thread_cannot_pollute_game_index(world):
    _,client,_,_=world
    client.thread(4,game_id=1)
    assert not client.search_cached_posts(1,'stacking')['matches']


def test_long_quote_is_indexed_without_clipping_original(world):
    api,client,svc,_=world
    body='[q="Designer"]'+'x '*300+'hiddenkeyword[/q]Other answer.'
    api.posts[4]=[(201,'someone',body)]
    svc.sync([4],2)
    hit=client.search_cached_posts(1,'hiddenkeyword')['matches'][0]
    assert hit['post']['body']==body


def test_status_does_not_create_index(world):
    _,client,svc,_=world
    assert svc.status()['counts']['posts']==0
    assert not client.index_path.exists()


def test_legacy_database_rows_without_originals_are_not_verified(world):
    _,client,_,_=world
    with LocalIndex(client.index_path) as index:
        index.register_forums(1,[{'id':'2'}])
        index.register_threads(2,[{'id':'3'}])
        index.store.put_posts(3,[dict(post_id=42,username='Designer',postdate='2026-08-01',editdate='',
            numedits=0,subject='Question',body_html='retreat',body_text='retreat')])
    assert not client.search_cached_posts(1,'retreat')['matches']


def test_mcp_cached_search_uses_same_index(world):
    from wgu.bgg_mcp import create_server
    _,client,svc,_=world
    svc.sync([4],2)
    server=create_server(client)
    async def run():
        value=await server.call_tool('bgg_search_cached_posts',dict(game_id=1,query='stacking'))
        # FastMCP returns content blocks (and a structured value on newer SDK 1.x).
        blocks=value[0] if isinstance(value,tuple) else value
        result=json.loads(blocks[0].text)
        assert result['data']['matches'][0]['post']['metadata']['id']=='201'
        assert result['data']['network_requests']==0
    asyncio.run(run())


@pytest.mark.parametrize('args',[['-m','wgu.bgg_mcp'],['wgu.py','mcp'],['wgu.py','bgg','serve']])
def test_stdio_entry_points_offline(world,args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    _,client,svc,_=world
    svc.sync([4],2)
    env=dict(os.environ,BGG_OFFLINE='1',BGG_INDEX_PATH=str(client.index_path))
    env.pop('BGG_API_TOKEN',None)
    env.pop('WGU_BGG_TOKEN',None)
    async def run():
        params=StdioServerParameters(command=sys.executable,args=args,env=env,
                                    cwd=str(Path(__file__).resolve().parents[1]))
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                reply=await session.call_tool('bgg_search_cached_posts',dict(game_id=1,query='stacking'))
                assert not reply.isError
                value=json.loads(reply.content[0].text)
                assert value['data']['network_requests']==0
                assert value['data']['matches'][0]['post']['metadata']['id']=='201'
    asyncio.run(asyncio.wait_for(run(),timeout=20))


def test_mcp_uses_project_index(tmp_path,monkeypatch):
    from wgu import bgg_mcp
    (tmp_path/'wgu.yaml').write_text('game: {id: test}\nbgg: {thing_id: 1, cache: build/bgg}\n',encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    seen=[]
    original=BGGClient
    def factory(**kwargs):
        seen.append(kwargs['index_path'])
        return original(**kwargs)
    monkeypatch.setattr(bgg_mcp,'BGGClient',factory)
    bgg_mcp.create_server()
    assert seen==[tmp_path/'build/bgg/bgg.sqlite']


def test_cli_offline_and_missing_selection(world,tmp_path):
    api,client,svc,_=world
    svc.sync([4],2)
    (tmp_path/'wgu.yaml').write_text('game: {id: test}\nbgg: {thing_id: 1}\n',encoding='utf-8')
    env=dict(os.environ,BGG_OFFLINE='1',BGG_INDEX_PATH=str(client.index_path),PYTHONIOENCODING='utf-8')
    command=[sys.executable,str(Path(__file__).resolve().parents[1]/'wgu.py'),'-C',str(tmp_path),'bgg']
    result=subprocess.run(command+['search','stacking'],env=env,text=True,encoding='utf-8',capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['data']['matches'][0]['post']['metadata']['id']=='201'
    missing=subprocess.run(command+['sync'],env=env,text=True,encoding='utf-8',capture_output=True,timeout=20)
    assert missing.returncode==2 and '--threads' in missing.stderr


def test_empty_append_keeps_cursor_and_stale_cursor_is_rejected(world,monkeypatch):
    api,client,svc,_=world
    svc.sync([4],2)
    assert client.thread(4,min_article_id=202,game_id=1)['next_min_article_id']==202
    from defusedxml import ElementTree as ET
    monkeypatch.setattr(client,'xml',lambda *args,**kwargs: ET.fromstring(
        '<thread><articles><article id="201"><body>old page</body></article></articles></thread>'))
    with pytest.raises(BGGError,match='kursora'): client.thread(4,min_article_id=202,game_id=1)


def test_mcp_sync_and_fts_share_client(world):
    from wgu.bgg_mcp import create_server
    api,client,_,_=world
    server=create_server(client)
    async def run():
        value=await server.call_tool('bgg_sync',dict(game_id=1,forum_id=2,thread_ids=[4],max_batches=1))
        blocks=value[0] if isinstance(value,tuple) else value
        assert json.loads(blocks[0].text)['data']['complete']
        assert client.search_cached_posts(1,'stacking')['matches']
    asyncio.run(run())
    assert [e for e,_ in api.calls]==['forumlist','forum','thread']
