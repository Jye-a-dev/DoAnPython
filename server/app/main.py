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
    ai_gateway_bp,
    ai_logs_bp,
    auth_bp,
    card_tags_bp,
    cards_bp,
    categories_bp,
    decks_bp,
    documents_bp,
    favorites_bp,
    folders_bp,
    profiles_bp,
    study_bp,
    system_bp,
    tags_bp,
    users_bp,
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SWAGGER"] = {
        "title": "Flashcard Server API - 3NF Architecture",
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
            "title": "EduFlash AI Backend API - 13 Tables 3NF Architecture",
            "description": (
                "Hệ thống RESTful CRUD API hoàn chỉnh cho 13 bảng theo chuẩn SQLite 3NF: "
                "Users, User Profiles, Categories, Folders, Documents (In-Memory BLOB), Decks, "
                "Cards, Tags, Card Tags (M:N), Study Sessions, Study Reviews (SM-2 Spaced Repetition), "
                "User Favorites và AI Generation Logs; tích hợp AI Pipeline Gateway."
            ),
            "version": "2.0.0",
            "contact": {
                "name": "EduFlash AI Development Team",
            },
        },
        "basePath": "/",
        "schemes": ["http"],
        "tags": [
            {
                "name": "Auth",
                "description": "Xác thực tài khoản và cấp phiên làm việc",
            },
            {
                "name": "AI Generator",
                "description": "Tiến trình sinh Q&A flashcards tự động và bóc băng âm thanh với AI Pipeline",
            },
            {
                "name": "System",
                "description": "Healthcheck Server, SQLite DB và ping AI Pipeline; giám sát CPU, RAM, mạng",
            },
            {
                "name": "Users & Profiles",
                "description": "Quản lý tài khoản người dùng (users) và hồ sơ cá nhân (user_profiles)",
            },
            {
                "name": "Categories",
                "description": "Quản lý danh mục phân loại bài học (categories)",
            },
            {
                "name": "Folders",
                "description": "Quản lý thư mục cây phân cấp (folders)",
            },
            {
                "name": "Documents",
                "description": "Quản lý và upload tài liệu in-memory BLOB, chống trùng content_hash (documents)",
            },
            {
                "name": "Decks",
                "description": "Quản lý bộ thẻ ghi nhớ (decks)",
            },
            {
                "name": "Cards & Tags",
                "description": "Quản lý thẻ flashcards (cards), nhãn (tags) và bảng liên kết (card_tags)",
            },
            {
                "name": "Study & SRS Reviews",
                "description": "Quản lý phiên học (study_sessions) và thuật toán lặp lại ngắt quãng SM-2 (study_reviews)",
            },
            {
                "name": "User Favorites",
                "description": "Quản lý danh sách yêu thích decks và flashcards của người dùng (user_favorites)",
            },
            {
                "name": "AI Logs",
                "description": "Nhật ký telemetry tiến trình sinh thẻ AI (ai_generation_logs)",
            },
        ],
        "definitions": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "username": {"type": "string", "example": "student01"},
                    "email": {"type": "string", "example": "student01@eduflash.ai"},
                    "role": {"type": "string", "example": "user"},
                    "is_active": {"type": "boolean", "example": True},
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                    "updated_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "UserProfile": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "display_name": {"type": "string", "example": "Nguyễn Văn A"},
                    "full_name": {"type": "string", "example": "Nguyễn Văn A"},
                    "avatar_url": {
                        "type": "string",
                        "example": "https://avatar.iran.liara.run/public/1",
                    },
                    "bio": {
                        "type": "string",
                        "example": "Sinh viên đam mê học ngoại ngữ",
                    },
                    "timezone": {"type": "string", "example": "Asia/Ho_Chi_Minh"},
                    "daily_card_goal": {"type": "integer", "example": 20},
                },
            },
            "Category": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Khoa học máy tính"},
                    "description": {"type": "string", "example": "Chuyên ngành IT"},
                    "color_code": {"type": "string", "example": "#3B82F6"},
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "Folder": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "category_id": {"type": "integer", "example": 1},
                    "parent_id": {"type": "integer", "example": None},
                    "name": {"type": "string", "example": "Cấu trúc dữ liệu"},
                    "description": {
                        "type": "string",
                        "example": "Ngăn xếp, hàng đợi, cây",
                    },
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "Document": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "filename": {"type": "string", "example": "python_basics.pdf"},
                    "file_type": {"type": "string", "example": "pdf"},
                    "file_size_bytes": {"type": "integer", "example": 1048576},
                    "content_hash": {"type": "string", "example": "a1b2c3d4e5f6..."},
                    "extracted_text": {
                        "type": "string",
                        "example": "Văn bản bài học trích xuất...",
                    },
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "Deck": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "folder_id": {"type": "integer", "example": 1},
                    "category_id": {"type": "integer", "example": 1},
                    "title": {"type": "string", "example": "Python OOP"},
                    "description": {
                        "type": "string",
                        "example": "Bộ câu hỏi hướng đối tượng",
                    },
                    "is_public": {"type": "boolean", "example": False},
                    "card_count": {"type": "integer", "example": 25},
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "Card": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "deck_id": {"type": "integer", "example": 1},
                    "document_id": {"type": "integer", "example": 1},
                    "question": {
                        "type": "string",
                        "example": "Python là ngôn ngữ biên dịch hay thông dịch?",
                    },
                    "answer": {
                        "type": "string",
                        "example": "Thông dịch (thông qua Bytecode)",
                    },
                    "explanation": {
                        "type": "string",
                        "example": "CPython biên dịch mã nguồn thành bytecode rồi thực thi trên VM.",
                    },
                    "difficulty": {"type": "string", "example": "medium"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["python", "basics"],
                    },
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "Tag": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "python"},
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "StudySession": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "deck_id": {"type": "integer", "example": 1},
                    "started_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                    "ended_at": {"type": "string", "example": None},
                    "total_reviewed": {"type": "integer", "example": 10},
                },
            },
            "StudyReview": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "session_id": {"type": "integer", "example": 1},
                    "card_id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "review_rating": {"type": "integer", "example": 3},
                    "ease_factor": {"type": "number", "example": 2.5},
                    "interval_days": {"type": "integer", "example": 1},
                    "repetitions": {"type": "integer", "example": 1},
                    "next_review_date": {
                        "type": "string",
                        "example": "2026-10-29T02:00:00",
                    },
                    "reviewed_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "UserFavorite": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "deck_id": {"type": "integer", "example": 1},
                    "card_id": {"type": "integer", "example": None},
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
            "AIGenerationLog": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "document_id": {"type": "integer", "example": 1},
                    "deck_id": {"type": "integer", "example": 1},
                    "model_name": {"type": "string", "example": "flan-t5-base"},
                    "cards_generated": {"type": "integer", "example": 5},
                    "inference_time_seconds": {"type": "number", "example": 1.45},
                    "prompt_tokens": {"type": "integer", "example": 150},
                    "completion_tokens": {"type": "integer", "example": 60},
                    "status": {"type": "string", "example": "SUCCESS"},
                    "error_message": {"type": "string", "example": None},
                    "created_at": {"type": "string", "example": "2026-10-28T02:00:00"},
                },
            },
        },
    }

    # Khởi tạo và đồng bộ schema cơ sở dữ liệu SQLite
    init_db(app)

    # Đăng ký toàn bộ Blueprints CRUD cho 13 Tables + AI Gateway
    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_gateway_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(decks_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(card_tags_bp)
    app.register_blueprint(study_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(ai_logs_bp)

    Swagger(app, config=swagger_config, template=swagger_template)

    @app.teardown_request
    def teardown_db_session(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

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
    print("✨ Flashcard Backend Server - 3NF Architecture")
    print(f"🚀 Running on: http://127.0.0.1:{port}")
    print(f"📖 Swagger Docs: http://127.0.0.1:{port}/docs/")
    print(f"⚙️  API Endpoint: http://127.0.0.1:{port}/api")
    print("=" * 60)
    app.run(host=host, port=port, debug=True)
