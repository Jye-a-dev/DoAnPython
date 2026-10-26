"""
profiles.py — User Profiles CRUD API endpoints (Table 2: user_profiles).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.user import UserProfile

profiles_bp = Blueprint("profiles", __name__, url_prefix="/api/profiles")


@profiles_bp.route("", methods=["GET"])
def list_profiles():
    """Lấy danh sách hồ sơ người dùng (Table 2: user_profiles)"""
    user_id = request.args.get("user_id", type=int)
    query = UserProfile.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    profiles = query.order_by(UserProfile.id.asc()).all()
    return jsonify([p.to_dict() for p in profiles]), 200


@profiles_bp.route("", methods=["POST"])
def create_profile():
    """Tạo mới hồ sơ người dùng (Table 2: user_profiles)"""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400
    if UserProfile.query.filter_by(user_id=user_id).first():
        return jsonify({"error": "Hồ sơ của người dùng này đã tồn tại"}), 409
    profile = UserProfile(
        user_id=user_id,
        display_name=data.get("display_name"),
        full_name=data.get("full_name"),
        avatar_url=data.get("avatar_url"),
        bio=data.get("bio"),
        timezone=data.get("timezone", "UTC"),
        daily_card_goal=int(data.get("daily_card_goal", 20)),
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify(profile.to_dict()), 201


@profiles_bp.route("/<int:profile_id>", methods=["GET"])
def get_profile_by_id(profile_id: int):
    """Lấy thông tin chi tiết một hồ sơ theo profile_id (Table 2: user_profiles)"""
    profile = db.session.get(UserProfile, profile_id)
    if not profile:
        return jsonify({"error": f"Không tìm thấy hồ sơ ID {profile_id}"}), 404
    return jsonify(profile.to_dict()), 200


@profiles_bp.route("/<int:profile_id>", methods=["PUT"])
def update_profile_by_id(profile_id: int):
    """Cập nhật thông tin hồ sơ người dùng (Table 2: user_profiles)"""
    profile = db.session.get(UserProfile, profile_id)
    if not profile:
        return jsonify({"error": f"Không tìm thấy hồ sơ ID {profile_id}"}), 404
    data = request.get_json(silent=True) or {}
    for field in [
        "display_name",
        "full_name",
        "avatar_url",
        "bio",
        "timezone",
        "daily_card_goal",
    ]:
        if field in data:
            setattr(profile, field, data[field])
    db.session.commit()
    return jsonify(profile.to_dict()), 200


@profiles_bp.route("/<int:profile_id>", methods=["DELETE"])
def delete_profile_by_id(profile_id: int):
    """Xóa hồ sơ người dùng (Table 2: user_profiles)"""
    profile = db.session.get(UserProfile, profile_id)
    if not profile:
        return jsonify({"error": f"Không tìm thấy hồ sơ ID {profile_id}"}), 404
    try:
        db.session.delete(profile)
        db.session.commit()
        return jsonify({"message": f"Đã xóa hồ sơ ID {profile_id} thành công"}), 200
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa hồ sơ: {str(err)}"}), 500
