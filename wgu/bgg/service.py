"""Project CLI facade over the same bounded client used by MCP."""
import os
from .client import BGGClient, BGGError, positive
from .index import LocalIndex
from ..bgg_authority import AuthorityRegistry


def settings(project):
    cfg=dict(project.data.get('bgg') or {})
    cfg.setdefault('thing_id',None)
    cfg.setdefault('cache','build/bgg')
    return cfg


class Bgg:
    def __init__(self, project, client=None):
        self.project=project
        self.cfg=settings(project)
        self.cache_path=project.root / self.cfg['cache'] / 'bgg.sqlite'
        self.client=client or BGGClient(index_path=self.cache_path)

    def close(self):
        pass  # Connections are scoped to each operation.

    def thing_id(self, game_id=None):
        value=game_id if game_id is not None else self.cfg.get('thing_id')
        if value is None:
            raise BGGError('Ustaw bgg.thing_id w wgu.yaml lub podaj --thing ID.')
        return positive(value)

    def search_games(self, query): return self.client.search_games(query)
    def game(self, thing_id=None): return self.client.game(self.thing_id(thing_id))

    def forums(self, thing_id=None):
        tid=self.thing_id(thing_id)
        self.client.forums(tid)
        with self.client.local_index() as index:
            return dict(thing_id=tid,forums=index.store.forums(tid),stale=False)

    def threads(self, forum_id, page=1):
        return self.client.threads(forum_id,page)

    def thread(self, thread_id, count=100, min_article_id=1):
        return self.client.thread(thread_id,count,min_article_id,self.thing_id())

    def sync(self, thread_ids, forum_id, max_batches=1, page=1, thing_id=None):
        """Only explicit threads on one verified forum page; no bulk forum sync."""
        tid=self.thing_id(thing_id)
        positive(forum_id)
        positive(page,10000)
        positive(max_batches,5)
        if not thread_ids or len(thread_ids)>5 or len(set(thread_ids))!=len(thread_ids):
            raise ValueError('Wskaż 1–5 różnych ID wątków; pełny zrzut forum jest wyłączony.')
        for selected in thread_ids: positive(selected)
        if str(forum_id) not in {f['id'] for f in self.client.forums(tid)}:
            raise ValueError('Forum nie należy do wskazanej gry.')
        listing=self.client.threads(forum_id,page)
        if not set(thread_ids).issubset({int(t['id']) for t in listing}):
            raise ValueError('Wątki muszą należeć do wskazanej strony forum.')
        batches=0
        visited=[]
        pending=[]
        for thread_id in thread_ids:
            with self.client.local_index() as index:
                cursor=index.store.meta(f'cursor:{tid}:{thread_id}',dict(next_min_article_id=1,complete=False))
                if cursor['complete'] and cursor.get('lastpostdate')==index.store.thread(thread_id)['lastpostdate']:
                    continue
            article_id=cursor['next_min_article_id']
            while True:
                if batches==max_batches:
                    pending.append(thread_id)
                    break
                data=self.client.thread(thread_id,100,article_id,tid)
                batches+=1
                visited.append(dict(thread_id=thread_id,min_article_id=article_id,posts=len(data['posts'])))
                if not data['possibly_more']: break
                if data['next_min_article_id']<=article_id:
                    raise BGGError('BGG nie przesunęło pozycji wpisów; zatrzymano synchronizację.')
                article_id=data['next_min_article_id']
        return dict(game_id=tid,visited=visited,batches_scanned=batches,pending_thread_ids=pending,
                    complete=not pending,scope='Wybrane wątki, do 5 partii po 100 wpisów; metadane osobno.')

    def search_posts(self, query, thing_id=None, author_role=None, forum_id=None, limit=10):
        return self.client.search_cached_posts(self.thing_id(thing_id),query,forum_id,author_role,limit)

    def files(self, thing_id=None):
        tid=self.thing_id(thing_id)
        return dict(thing_id=tid,files_page=f'https://boardgamegeek.com/boardgame/{tid}/x/files',
                    errata=list(self.project.data.get('sources',{}).get('errata') or []))

    def authorities(self, thing_id=None):
        tid=self.thing_id(thing_id)
        registry=AuthorityRegistry()
        return dict(game_id=tid,registry_status=registry.status,
            entries=[e for e in registry.entries if e['game_id']==tid],
            warning='Role wyłącznie z BGG_AUTHORITY_FILE; bgg.authorities i nazwiska nie są dowodem.')

    def status(self):
        counts=dict.fromkeys(('games','forums','threads','posts','users'),0)
        if self.client.index_path.exists():
            with LocalIndex(self.client.index_path) as index: counts=index.store.counts()
        offline=os.environ.get('BGG_OFFLINE',os.environ.get('WGU_BGG_OFFLINE','0')) not in ('','0')
        online=not offline and bool(os.environ.get('BGG_API_TOKEN',os.environ.get('WGU_BGG_TOKEN','')))
        return dict(thing_id=self.cfg['thing_id'],online=online,offline_reason=None if online else 'offline lub brak BGG_API_TOKEN',
                    delay=5,cache=str(self.client.index_path),counts=counts)
