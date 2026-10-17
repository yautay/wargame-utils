"""Derived FTS index; originals and fresh authority assessments stay separate."""
import json

from .client import BGGError, search_text
from .store import Store
from .xmlapi import iso_utc
from ..bgg_authority import AuthorityRegistry

ROLES = {'unverified', 'designer', 'publisher_representative', 'community_member'}


class LocalIndex:
    def __init__(self, path):
        self.store = Store(path)
        self.store.db.execute('''CREATE TABLE IF NOT EXISTS source_posts(
            game_id INTEGER NOT NULL, post_id INTEGER NOT NULL, source_json TEXT NOT NULL,
            PRIMARY KEY(game_id, post_id))''')
        self.store.db.commit()

    def __enter__(self): return self

    def __exit__(self, *exc): self.store.close()

    def register_forums(self, game_id, forums):
        rows = []
        for f in forums:
            fid = int(f['id'])
            old = self.store.forum(fid)
            if old and old['thing_id'] != game_id:
                raise BGGError('Forum ma w indeksie inną grę; wymagany przegląd źródeł.')
            rows.append(dict(forum_id=fid, title=f.get('title', f.get('name', '')),
                numthreads=int(f.get('numthreads', 0)), numposts=int(f.get('numposts', 0)),
                lastpostdate=iso_utc(f.get('lastpostdate')), noposting=f.get('noposting') == '1'))
        self.store.put_forums(game_id, rows)

    def register_threads(self, forum_id, threads):
        forum = self.store.forum(forum_id)
        if not forum:
            return
        rows=[]
        for t in threads:
            tid=int(t['id'])
            self.check_game(tid, forum['thing_id'])
            rows.append(dict(thread_id=tid, subject=t.get('subject', ''), author=t.get('author', ''),
                numarticles=int(t.get('numarticles', 0)), postdate=iso_utc(t.get('postdate')),
                lastpostdate=iso_utc(t.get('lastpostdate'))))
        self.store.put_threads(forum_id, forum['thing_id'], rows)

    def check_game(self, thread_id, game_id):
        thread = self.store.thread(thread_id)
        if thread and thread['thing_id'] is not None and thread['thing_id'] != game_id:
            raise BGGError('Wątek nie należy do wskazanej gry.')
        return bool(thread and thread['thing_id'] == game_id)

    def ingest(self, game_id, thread_id, data, min_article_id=1):
        if not self.check_game(thread_id, game_id):
            return False
        rows=[]
        originals=[]
        for p in data['posts']:
            m=p['metadata']
            original={k:p[k] for k in ('metadata','body','subject','url') if k in p}
            originals.append((game_id, int(m['id']), json.dumps(original, ensure_ascii=False)))
            rows.append(dict(post_id=int(m['id']), username=m.get('username',''),
                postdate=m.get('postdate',''), editdate=m.get('editdate',''),
                numedits=int(m.get('numedits',0)), subject=p.get('subject',''),
                body_html=p['body'], body_text=search_text(p['body'])))
        with self.store.db:
            for original in originals:
                self.store.db.execute('INSERT OR REPLACE INTO source_posts VALUES (?,?,?)',
                                      original)
            self.store.put_posts(thread_id, rows)
        key=f'cursor:{game_id}:{thread_id}'
        previous=self.store.meta(key, {'next_min_article_id':1})
        if min_article_id == 1 or min_article_id == previous['next_min_article_id']:
            cursor=dict(next_min_article_id=data['next_min_article_id'], complete=not data['possibly_more'],
                        lastpostdate=self.store.thread(thread_id)['lastpostdate'])
            self.store.set_meta(key,cursor)
        return True

    def original(self, game_id, post_id):
        row=self.store.db.execute('SELECT source_json FROM source_posts WHERE game_id=? AND post_id=?',
                                 (game_id,post_id)).fetchone()
        return json.loads(row[0]) if row else None

    def search(self, game_id, query, forum_id=None, author_role=None, limit=10):
        if author_role is not None and author_role not in ROLES:
            raise ValueError('Filtr roli wymaga: '+', '.join(sorted(ROLES)))
        candidates=self.store.search(query,game_id,forum_id,limit=max(1,self.store.counts()['posts']))
        registry=AuthorityRegistry()
        matches=[]
        for h in candidates:
            original=self.original(game_id,h['post_id'])
            if original is None:
                continue
            registry.annotate([original],game_id)
            if author_role is not None and original['authority'] != author_role:
                continue
            matches.append(dict(thread_id=h['thread_id'],forum_id=h['forum_id'],
                subject=h['thread_subject'],post=original,score=h['score'],snippet=h['snippet']))
            if len(matches)==limit:
                break
        count=self.store.db.execute('SELECT COUNT(*) FROM source_posts WHERE game_id=?',(game_id,)).fetchone()[0]
        return dict(matches=matches,source_posts_in_index=count,network_requests=0,
            scope='Wyłącznie lokalny indeks już pobranych wpisów; brak trafień nie dowodzi braku odpowiedzi na BGG.',
            warning='Stare wiersze bez oryginalnych metadanych wymagają celowanego odświeżenia.')
