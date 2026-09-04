import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path when imported as backend.app on Vercel
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config, IS_VERCEL, _safe_int
from utils.database import init_db, check_db_connection

# Blueprints
from routes.auth import auth_bp
from routes.scan import scan_bp
from routes.ai import ai_bp
from routes.history import history_bp
from routes.health_records import health_records_bp
from routes.reports import reports_bp
from routes.profile import profile_bp
from routes.ambulance import ambulance_bp
from routes.sos import sos_bp
from routes.qr import qr_bp


def create_app():
    base = Path(__file__).resolve().parent
    frontend_candidates = [
        base.parent / "frontend",
        base / "frontend",
        Path("/var/task/frontend"),
        Path.cwd() / "frontend"
    ]
    frontend_dir = str(base.parent / "frontend")
    for cand in frontend_candidates:
        if cand.exists() and (cand / "index.html").exists():
            frontend_dir = str(cand)
            break

    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    app.config.from_object(Config)

    # Attempt non-blocking MongoDB index setup
    try:
        init_db()
    except Exception as e:
        print(f"[Database] Warning: MongoDB index initialization skipped: {e}")

    # Configure CORS for local development and production
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"]
    )

    # Register Production Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(health_records_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(ambulance_bp)
    app.register_blueprint(sos_bp)
    app.register_blueprint(qr_bp)

    # Root & Health Endpoints
    @app.route("/")
    def index():
        try:
            index_path = Path(app.static_folder) / "index.html"
            if index_path.exists():
                return send_from_directory(app.static_folder, "index.html")
        except Exception:
            pass
        return jsonify({
            "service": "CareConnect",
            "version": "2.0.0",
            "status": "online",
            "database": "MongoDB Atlas",
            "message": "CareConnect AI-Powered Healthcare Assistance Platform is running 🚑"
        })

    @app.route("/health", methods=["GET"])
    def health():
        """Standard health check endpoint"""
        return jsonify({
            "status": "ok",
            "service": "CareConnect"
        }), 200

    @app.route("/db-health", methods=["GET"])
    def db_health():
        """Database connectivity & health verification endpoint (MongoDB)"""
        is_connected, message, info = check_db_connection()
        if is_connected:
            return jsonify({
                "status": "ok",
                "database": "MongoDB connected",
                "users_count": info.get("users_count", 0),
                "service": "CareConnect"
            }), 200
        else:
            return jsonify({
                "status": "warning" if IS_VERCEL else "error",
                "database": message,
                "service": "CareConnect"
            }), 200 if IS_VERCEL else 500

    # Static file serving for uploaded scan images and reports
    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    @app.route("/<path:path>")
    def catch_all_static(path):
        clean = path
        while clean.startswith("frontend/"):
            clean = clean[len("frontend/"):]
        file_path = Path(app.static_folder) / clean
        if file_path.exists() and file_path.is_file():
            return send_from_directory(app.static_folder, clean)
        html_file = Path(app.static_folder) / f"{clean}.html"
        if html_file.exists() and html_file.is_file():
            return send_from_directory(app.static_folder, f"{clean}.html")
        return jsonify({"success": False, "message": "Resource not found."}), 404

    # Global Error Handlers (Always JSON)
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "message": "Bad request.", "error": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"success": False, "message": "Unauthorized access.", "error": str(e)}), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found.", "error": str(e)}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "An internal server error occurred.", "error": "INTERNAL_SERVER_ERROR"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = _safe_int(os.getenv("PORT"), 5000)
    app.run(host="0.0.0.0", port=port, debug=True)