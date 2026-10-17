"""Opt-in, selected BGG threads only. Never enabled by a token alone."""
import os

import pytest

from wgu.bgg import BGGClient
from wgu.bgg.service import Bgg
from types import SimpleNamespace


@pytest.mark.skipif(not (os.environ.get('BGG_ACCEPTANCE')=='1' and os.environ.get('BGG_ACCEPTANCE_THREADS')
                        and os.environ.get('BGG_API_TOKEN')),
                    reason='requires explicit BGG_ACCEPTANCE=1, token and selected thread IDs')
def test_selected_threads_only(tmp_path):
    game=int(os.environ['BGG_ACCEPTANCE_GAME'])
    forum=int(os.environ['BGG_ACCEPTANCE_FORUM'])
    ids=[int(x) for x in os.environ['BGG_ACCEPTANCE_THREADS'].split(',')]
    client=BGGClient(index_path=tmp_path/'index.sqlite')
    service=Bgg(SimpleNamespace(root=tmp_path,data={'bgg':{'thing_id':game}}),client)
    report=service.sync(ids,forum,max_batches=1,page=int(os.environ.get('BGG_ACCEPTANCE_PAGE','1')))
    assert report['batches_scanned']<=1
    assert all(v['thread_id'] in ids for v in report['visited'])
    print(report)
