"""
Shared test fixtures.

Redirects drift_store to a temporary file so tests don't pollute
the real logs/drift_events.jsonl used by Docker builds.
"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _isolate_drift_store(tmp_path):
    """Redirect the global drift_store to a temp file for every test."""
    tmp_log = tmp_path / "drift_events.jsonl"
    with patch("app.drift_store.DRIFT_LOG_PATH", tmp_log):
        # Re-point the existing global instance
        from app.drift_store import drift_store

        original_path = drift_store.log_path
        drift_store.log_path = tmp_log
        yield
        drift_store.log_path = original_path
