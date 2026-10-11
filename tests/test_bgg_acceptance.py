"""Acceptance test against the real BGG XML API2 (Ukraine '43, thing 3263, forums 63–69).

Skipped unless WGU_BGG_TOKEN is set and WGU_BGG_ACCEPTANCE=1. A full first sync takes ≈ 215 requests at 5 s
(≈ 18 min); the cache goes to WGU_BGG_ACCEPTANCE_DIR (default: a temporary directory), so a second run there is
incremental. Run:
    WGU_BGG_ACCEPTANCE=1 python -m pytest tests/test_bgg_acceptance.py -s
and copy the printed report into docs/research/bgg-mcp.md (section 8).
"""
import json
import os
from pathlib import Path

import pytest

from wgu.bgg.service import Bgg
from wgu.config import DEFAULTS, Project, _merge

pytestmark = pytest.mark.skipif(not (os.environ.get("WGU_BGG_TOKEN") and os.environ.get("WGU_BGG_ACCEPTANCE") == "1"),
                                reason="needs WGU_BGG_TOKEN and WGU_BGG_ACCEPTANCE=1 (real BGG XML API2)")


def test_ukraine43_retreat_priority_designer_post(tmp_path):
    root = Path(os.environ.get("WGU_BGG_ACCEPTANCE_DIR") or tmp_path)
    data = _merge(DEFAULTS, {"game": {"id": "ukraine43"}, "bgg": {
        "thing_id": 3263, "forums": [63, 64, 65, 66, 67, 68, 69],
        "authorities": [{"user": "Simon7itch", "role": "designer", "person": 140},
                        {"user": "tcurtis", "role": "designer", "person": 672}]}})
    svc = Bgg(Project(root, data))
    try:
        report = svc.sync(progress=print)
        print(json.dumps({k: v for k, v in report.items() if k != "forums"}, ensure_ascii=False))
        assert report["complete"]
        hits = svc.search_posts("retreat priority", limit=20)
        top = [h for h in hits if h["thread_id"] == 1679334 and h["username"] == "Simon7itch"]
        assert top, [(h["thread_id"], h["username"]) for h in hits]
        assert top[0]["role"] == "designer" and top[0]["postdate"].startswith("2016-12-17")
        print(f"search rank of the designer post: {hits.index(top[0]) + 1} of {len(hits)}; counts: {svc.store.counts()}")
    finally:
        svc.close()
