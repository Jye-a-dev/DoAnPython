"""
user_profile.py — User Profile endpoints (Table 2: user_profiles).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.user import User, UserProfile


def get_user_profile_by_user_id(user_id: int):
    """
    Lấy thông tin hồ sơ của người dùng (GET /api/users/{user_id}/profile)
    ---
    tags:
      - Users & Profiles
    summary: Lấy profile của user (display_name, bio, daily_card_goal, timezone)
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID người dùng
    responses:
      200:
        description: Hồ sơ cá nhân của người dùng
      404:
        description: Không tìm thấy người dùng hoặc hồ sơ
    """
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}), 404
        profile = UserProfile(user_id=user_id, display_name=user.username)
        db.session.add(profile)
        db.session.commit()

    return jsonify(profile.to_dict()), 200


def update_user_profile_by_user_id(user_id: int):
    """
    Cập nhật thông tin profile của người dùng (PUT /api/users/{user_id}/profile)
    ---
    tags:
      - Users & Profiles
    summary: Cập nhật thông tin profile của user
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID người dùng sở hữu profile
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            display_name:
              type: string
              example: Nguyễn Văn A
            full_name:
              type: string
              example: Nguyễn Văn A
            avatar_url:
              type: string
              example: https://avatar.iran.liara.run/public/12
            bio:
              type: string
              example: Sinh viên công nghệ thông tin
            timezone:
              type: string
              example: Asia/Ho_Chi_Minh
            daily_card_goal:
              type: integer
              example: 30
    responses:
      200:
        description: Cập nhật hồ sơ thành công
      404:
        description: Không tìm thấy người dùng
      500:
        description: Lỗi máy chủ
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}), 404

    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)

    data = request.get_json(silent=True) or {}
    updatable_fields = [
        "display_name",
        "full_name",
        "avatar_url",
        "bio",
        "timezone",
        "daily_card_goal",
    ]
    for field in updatable_fields:
        if field in data:
            if field == "daily_card_goal":
                setattr(profile, field, int(data[field]))
            else:
                setattr(profile, field, data[field])

    try:
        db.session.commit()
        return jsonify(profile.to_dict()), 200
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật hồ sơ: {str(err)}"}), 500


def register_user_profile_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/<int:user_id>/profile", view_func=get_user_profile_by_user_id, methods=["GET"])
    bp.add_url_rule("/<int:user_id>/profile", view_func=update_user_profile_by_user_id, methods=["PUT"])

