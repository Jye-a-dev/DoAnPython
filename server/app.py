import os
import sys
import threading
from pathlib import Path
from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
load_dotenv(SERVER_DIR / ".env")
load_dotenv()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from asgiref.wsgi import WsgiToAsgi
from flask import Flask, redirect, send_from_directory
from flask_cors import CORS
from flask_restx import Api

from server.core.config import (
    AUDIO_DIR,
    DEBUG,
    SERVER_HOST,
    SERVER_PORT,
    UPLOADS_DIR,
    cleanup_old_files_worker,
)
from server.database import init_db
from server.routers import all_namespaces, media_bp

flask_app = Flask(__name__)
flask_app.config["PROPAGATE_EXCEPTIONS"] = True
CORS(flask_app, resources={r"/*": {"origins": "*"}})
flask_app.register_blueprint(media_bp)

authorizations = {
    "Bearer": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "JWT Authorization header using Bearer scheme. Accepts both 'Bearer <token>' and raw '<token>'. Calling /api/v1/auth/login or /api/v1/auth/dev-token also sets session cookie automatically for all subsequent requests."
    }
}

api = Api(
    flask_app,
    version="2.1.0",
    title="Smart Object Detector & E-Commerce Gateway API",
    description="Flask API Gateway kết nối SQLite, AI Pipeline (YOLO/TTS) và E-Commerce Visual Search",
    doc="/docs",
    authorizations=authorizations,
    security="Bearer"
)

# Attach all modularized RESTX namespaces to Swagger UI
for ns in all_namespaces:
    api.add_namespace(ns)


@flask_app.route("/static/uploads/<path:filename>", methods=["GET"])
def native_serve_uploads(filename: str):
    """Serve uploaded images via standard Flask static routing."""
    return send_from_directory(str(UPLOADS_DIR), filename)


@flask_app.route("/static/audio/<path:filename>", methods=["GET"])
def native_serve_audio(filename: str):
    """Serve synthesized audio MP3s via standard Flask static routing."""
    return send_from_directory(str(AUDIO_DIR), filename)


@flask_app.route("/swagger")
def swagger_redirect():
    """Redirect legacy swagger path to interactive documentation."""
    return redirect("/docs")


_startup_lock = threading.Lock()
_startup_done = False


def ensure_startup_initialized():
    """Thread-safe lazy initializer for SQLite schema and purge workers."""
    global _startup_done
    if not _startup_done:
        with _startup_lock:
            if not _startup_done:
                init_db()
                if not DEBUG or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                    cleanup_thread = threading.Thread(target=cleanup_old_files_worker, daemon=True)
                    cleanup_thread.start()
                _startup_done = True


@flask_app.before_request
def before_request_hook():
    ensure_startup_initialized()


# ASGI adapter for ASGI servers (uvicorn runner)
app = WsgiToAsgi(flask_app)

if __name__ == "__main__":
    ensure_startup_initialized()
    flask_app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=DEBUG,
        use_reloader=DEBUG,
        threaded=True
    )
