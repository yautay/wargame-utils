"""Launcher that works without installation: python <plugin root>/wgu.py <command> …
(skills call it as  python "${CLAUDE_PLUGIN_ROOT}/wgu.py" …). After `pip install -e .` use `wgu` directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:  # UTF-8 output on Windows consoles
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from wgu.cli import main  # noqa: E402

main()
