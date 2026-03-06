import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cache_lib import should_refresh


class RefreshPolicyTests(unittest.TestCase):
    def test_should_refresh_respects_ttl(self):
        now = datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc)
        recent = (now - timedelta(days=1)).isoformat()
        stale = (now - timedelta(days=15)).isoformat()

        self.assertFalse(should_refresh(last_checked=recent, freshness="volatile", now=now, force=False))
        self.assertTrue(should_refresh(last_checked=stale, freshness="volatile", now=now, force=False))

    def test_force_overrides_policy(self):
        now = datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc)
        recent = (now - timedelta(days=1)).isoformat()
        self.assertTrue(should_refresh(last_checked=recent, freshness="stable", now=now, force=True))


if __name__ == "__main__":
    unittest.main()
