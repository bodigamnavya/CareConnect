import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from utils.database import init_db, query_db, get_db_connection

# Blueprints
from routes.auth import auth_bp
from routes.scan import scan_bp
from routes.ai import ai_bp
from routes.history import history_bp
from routes.health_records import health_records_bp
from routes.reports import reports_bp
from routes.profile import profile_bp

def create_app():
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    app.config.from_object(Config)

    # Initialize Database Schema
    init_db()

    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": Config.FRONTEND_URL, "allow_headers": ["Content-Type", "Authorization"]}})

    # Register Production Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(health_records_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(profile_bp)

    # Root & Health Endpoints
    @app.route("/")
    def index():
        return jsonify({
            "service": "CareConnect",
            "version": "2.0.0",
            "status": "online",
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
        """Database connectivity & table readiness verification endpoint"""
        try:
            conn, db_type = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users;")
            cursor.close()
            conn.close()
            return jsonify({
                "status": "ok",
                "database": f"{db_type.capitalize()} connected",
                "service": "CareConnect"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "database": "Database connection failed",
                "error": str(e)
            }), 500

    # Static file serving for uploads
    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    # Global Error Handlers
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
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)