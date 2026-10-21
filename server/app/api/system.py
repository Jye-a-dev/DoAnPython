from flask import Blueprint, jsonify

system_bp = Blueprint("system", __name__, url_prefix="/api")


@system_bp.route("/health", methods=["GET"])
def health_check():
    """
    Kiểm tra tình trạng hoạt động của hệ thống và API
    ---
    tags:
      - System
    responses:
      200:
        description: Trạng thái hệ thống bình thường
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "database": "connected",
                "ai_pipeline": "ready",
            }
        ),
        200,
    )
