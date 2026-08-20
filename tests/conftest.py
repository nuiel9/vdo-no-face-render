"""Test bootstrap: repo root on sys.path, and placeholder AIVDO credentials.

`render.py` reads AIVDO_URL/AIVDO_API_KEY from os.environ at import time via
bracket access, so importing it with no environment raises KeyError before a
single test runs. These placeholders make `python3 -m pytest tests/` work from
a cold clone. setdefault, not assignment, so a real environment is preserved.
No test makes a network call; nothing here reaches AIVDO.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("AIVDO_URL", "http://test.invalid")
os.environ.setdefault("AIVDO_API_KEY", "test-key-not-real")
