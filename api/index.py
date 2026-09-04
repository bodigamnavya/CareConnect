import os
import sys
import tempfile
from pathlib import Path

# Resolve absolute paths
api_dir = Path(__file__).resolve().parent
root_dir = api_dir.parent
backend_dir = root_dir / "backend"

# Ensure backend directory is first in sys.path
for path_to_add in [str(backend_dir), str(root_dir)]:
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)

# Explicitly set VERCEL environment flag
os.environ["VERCEL"] = "1"

# Import Flask app
try:
    from app import app
except ImportError:
    from backend.app import app

# Vercel entry point
# Flask app object is exposed as 'app'
