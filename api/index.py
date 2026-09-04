import os
import sys
import traceback
from pathlib import Path

# Resolve paths
api_dir = Path(__file__).resolve().parent
root_dir = api_dir.parent
backend_dir = root_dir / "backend"

for p in [str(backend_dir), str(root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["VERCEL"] = "1"


class VercelPathMiddleware:
    """
    Strips internal Vercel serverless script prefixes from WSGI PATH_INFO so Flask routes match cleanly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        for prefix in ["/api/index.py", "/api/index", "/backend/app.py", "/backend/app"]:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break

        if not path:
            path = "/"

        environ["PATH_INFO"] = path
        return self.wsgi_app(environ, start_response)


app = None
init_error = None

try:
    from app import app as flask_app
    app = VercelPathMiddleware(flask_app)
except Exception as e:
    init_error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    print(f"[Vercel Initialization Error]: {init_error}")

if app is None:
    from flask import Flask, jsonify
    emergency_app = Flask(__name__)

    @emergency_app.route("/", defaults={"path": ""})
    @emergency_app.route("/<path:path>")
    def fallback_handler(path):
        return jsonify({
            "success": False,
            "error": "Serverless function initialization error",
            "details": init_error,
            "service": "CareConnect"
        }), 500

    app = emergency_app
