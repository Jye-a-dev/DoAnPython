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

# Configure sys.path so 'app' and 'pipeline' can be imported regardless of execution cwd
_SERVER_DIR = Path(__file__).resolve().parent.parent  # server/
_PROJECT_ROOT = _SERVER_DIR.parent  # workspace root
_PIPELINE_DIR = _PROJECT_ROOT / "pipeline"

for _path in [str(_SERVER_DIR), str(_PROJECT_ROOT), str(_PIPELINE_DIR)]:
    if _path not in sys.path:
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
from app.api.routes import api_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SWAGGER"] = {
        "title": "Flashcard AI Pipeline API",
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
            "title": "Flashcard AI Pipeline API",
            "description": (
                "Hệ thống API trích xuất và sinh câu hỏi flashcard tự động từ bài học "
                "bằng mô hình AI Flan-T5, đồng thời quản lý lưu trữ thẻ ghi nhớ qua SQLite."
            ),
            "version": "1.0.0",
            "contact": {
                "name": "Flashcard AI Support Team",
            },
        },
        "basePath": "/",
        "schemes": ["http"],
        "tags": [
            {
                "name": "Flashcards",
                "description": "Quản lý dữ liệu thẻ ghi nhớ (Flashcards)",
            },
            {
                "name": "AI Pipeline",
                "description": "Tiến trình sinh câu hỏi tự động với AI Flan-T5",
            },
            {
                "name": "System",
                "description": "Kiểm tra tình trạng hoạt động của dịch vụ",
            },
        ],
        "definitions": {
            "Flashcard": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "question": {
                        "type": "string",
                        "example": "Thủ đô của Việt Nam là thành phố nào?",
                    },
                    "answer": {
                        "type": "string",
                        "example": "Hà Nội",
                    },
                },
            },
            "GenerateRequest": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {
                        "type": "string",
                        "example": (
                            "Hà Nội là thủ đô của nước Cộng hòa Xã hội chủ nghĩa Việt Nam, "
                            "đồng thời là thành phố lớn nhất Việt Nam về diện tích với 3.359,82 km2."
                        ),
                        "description": "Nội dung bài học hoặc tài liệu cần trích xuất câu hỏi flashcards",
                    }
                },
            },
            "GenerateResponse": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "example": 1},
                    "cards": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/Flashcard"},
                    },
                },
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Văn bản bài học không được để trống",
                    }
                },
            },
            "MessageResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Đã xóa flashcard thành công",
                    }
                },
            },
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "healthy"},
                    "database": {"type": "string", "example": "connected"},
                    "ai_pipeline": {"type": "string", "example": "ready"},
                },
            },
        },
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    init_db(app)

    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return redirect("/docs/")

    @app.route("/apidocs")
    @app.route("/apidocs/")
    def apidocs():
        return redirect("/docs/")

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app = create_app()
    print("=" * 60)
    print("✨ Flashcard AI Pipeline Server")
    print(f"🚀 Running on: http://127.0.0.1:{port}")
    print(f"📖 Swagger Docs: http://127.0.0.1:{port}/docs/")
    print(f"⚙️  API Endpoint: http://127.0.0.1:{port}/api")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)
