"""Compatibility package for existing app.main:app commands. Source lives in backend/app."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parents[1] / "backend" / "app")]
