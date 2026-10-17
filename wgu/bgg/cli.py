"""CLI over the shared bounded BGG client; search is local only."""
from .render import result
import sys
from .client import BGGError

ACTIONS=['status','game','forums','threads','thread','sync','search','files','authorities','search-games','serve']


def add_parser(sp):
    p=sp.add_parser('bgg',help='BGG XML API2 + lokalny indeks FTS5')
    p.add_argument('action',choices=ACTIONS)
    p.add_argument('args',nargs='*')
    p.add_argument('--thing',type=int)
    p.add_argument('--page',type=int,default=1)
    p.add_argument('--forum',type=int)
    p.add_argument('--threads',help='1–5 ID wątków oddzielonych przecinkami, wymagane dla sync')
    p.add_argument('--max-batches',type=int,default=1)
    p.add_argument('--min-article-id',type=int,default=1)
    p.add_argument('--count',type=int,default=100)
    p.add_argument('--limit',type=int,default=10)
    p.add_argument('--role',choices=['designer','publisher_representative','community_member','unverified'])
    return p


def run(a,project_loader):
    if a.action=='serve':
        from ..bgg_mcp import main
        main([])
        return 0
    from .service import Bgg
    svc=Bgg(project_loader())
    try:
        if a.thing is not None: svc.cfg['thing_id']=a.thing
        data=_dispatch(svc,a)
    except (BGGError,ValueError) as exc:
        print(str(exc),file=sys.stderr)
        return 2
    finally:
        svc.close()
    print(result(data))
    return 0


def _dispatch(svc,a):
    if a.action=='status': return svc.status()
    if a.action=='game': return svc.game()
    if a.action=='forums': return svc.forums()
    if a.action=='authorities': return svc.authorities()
    if a.action=='files': return svc.files()
    if a.action=='search':
        return svc.search_posts(' '.join(a.args),author_role=a.role,forum_id=a.forum,limit=a.limit)
    if a.action=='search-games': return svc.search_games(' '.join(a.args))
    if a.action in ('thread','threads'):
        if len(a.args)!=1: raise ValueError('Podaj jedno ID wątku lub forum.')
        ident=int(a.args[0])
        return svc.threads(ident,a.page) if a.action=='threads' else svc.thread(ident,a.count,a.min_article_id)
    if a.action=='sync':
        if not a.threads or a.forum is None: raise ValueError('sync wymaga --threads ID[,ID] i --forum ID; pełny zrzut jest wyłączony.')
        return svc.sync([int(x) for x in a.threads.split(',')],a.forum,a.max_batches,a.page)
    raise ValueError('Nieznana operacja BGG.')
