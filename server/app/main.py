import os
import sys
from pathlib import Path

# Fix Windows console UTF-8 output encoding for Vietnamese characters
if sys.platform == "win32":
    stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(stdout_reconfigure):
        stdout_reconfigure(encoding="utf-8", errors="replace")
    stderr_reconfigure = getattr(sys.stderr, "reconfigure", None)
    if callable(stderr_reconfigure):
        stderr_reconfigure(encoding="utf-8", errors="replace")

# Configure sys.path so 'app' (from server) and 'pipeline' can be imported regardless of execution cwd
_SERVER_DIR = Path(__file__).resolve().parent.parent  # server/
_PROJECT_ROOT = _SERVER_DIR.parent  # workspace root
_PIPELINE_DIR = _PROJECT_ROOT / "pipeline"

for _path in [str(_PIPELINE_DIR), str(_PROJECT_ROOT), str(_SERVER_DIR)]:
    if _path in sys.path:
        sys.path.remove(_path)
    sys.path.insert(0, _path)

# Fallback: include virtualenv site-packages if available
_SERVER_VENV = _SERVER_DIR / ".venv" / "Lib" / "site-packages"
if _SERVER_VENV.exists() and str(_SERVER_VENV) not in sys.path:
    sys.path.append(str(_SERVER_VENV))

from flask import Flask, redirect
from flask_cors import CORS
from flasgger import Swagger
from app.core.config import Config
from app.core.database import db, init_db
from app.api import (
    documents_bp,
    generator_bp,
    decks_bp,
    cards_bp,
    study_bp,
    system_bp,
    users_bp,
    profiles_bp,
    categories_bp,
    folders_bp,
    tags_bp,
    card_tags_bp,
    ai_logs_bp,
    favorites_bp,
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SWAGGER"] = {
        "title": "Flashcard Server API",
        "uiversion": 3,
        "openapi": "2.0",
    }
    CORS(app)
    db.init_app(app)

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/",
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Flashcard Server API",
            "description": (
                "Hệ thống API quản lý tài liệu học tập (Documents), bộ thẻ ghi nhớ (Decks), "
                "thẻ flashcards, phiên học thuật toán Spaced Repetition (SM-2) và Gateway AI."
            ),
            "version": "1.0.0",
            "contact": {
                "name": "Flashcard Server Team",
            },
        },
        "basePath": "/",
        "schemes": ["http"],
        "tags": [
            {
                "name": "Documents",
                "description": "Quản lý và upload tài liệu in-memory BLOB (PDF/TXT)",
            },
            {
                "name": "AI Generator",
                "description": "Tiến trình sinh câu hỏi tự động và bóc băng âm thanh với AI Pipeline",
            },
            {
                "name": "Decks",
                "description": "Quản lý bộ thẻ ghi nhớ (Decks)",
            },
            {
                "name": "Cards",
                "description": "Quản lý thẻ flashcards",
            },
            {
                "name": "Study",
                "description": "Phiên học và đánh giá Spaced Repetition (SM-2)",
            },
            {
                "name": "System",
                "description": "Kiểm tra tình trạng hoạt động của dịch vụ",
            },
        ],
    }

    # Khởi tạo và đồng bộ schema cơ sở dữ liệu
    init_db(app)

    # Đăng ký toàn bộ 14 Blueprints (13 Tables + Gateway AI)
    app.register_blueprint(documents_bp)
    app.register_blueprint(generator_bp)
    app.register_blueprint(decks_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(study_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(card_tags_bp)
    app.register_blueprint(ai_logs_bp)
    app.register_blueprint(favorites_bp)

    Swagger(app, config=swagger_config, template=swagger_template)

    @app.route("/")
    def index():
        return redirect("/docs/")

    @app.route("/apidocs")
    @app.route("/apidocs/")
    def apidocs():
        return redirect("/docs/")

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    host = os.getenv("HOST", "0.0.0.0")
    app = create_app()
    print("=" * 60)
    print("✨ Flashcard Backend Server")
    print(f"🚀 Running on: http://127.0.0.1:{port}")
    print(f"📖 Swagger Docs: http://127.0.0.1:{port}/docs/")
    print(f"⚙️  API Endpoint: http://127.0.0.1:{port}/api")
    print("=" * 60)
    app.run(host=host, port=port, debug=True)
