"""Repository-relative assets; independent of the process working directory."""
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
