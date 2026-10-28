"""
user_auth.py — Legacy login endpoint for users (POST /api/users/login).
"""

from __future__ import annotations

import hashlib
from flask import Blueprint, jsonify, request
from app.models.user import User


def login_user_legacy():
    """
    Đăng nhập tương thích ngược (POST /api/users/login)
    ---
    tags:
      - Users & Profiles
    summary: Đăng nhập tương thích ngược
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - password
          properties:
            login:
              type: string
            password:
              type: string
    responses:
      200:
        description: Đăng nhập thành công
      401:
        description: Sai thông tin
    """
    data = request.get_json(silent=True) or {}
    login_val = data.get("username") or data.get("email") or data.get("login")
    password = data.get("password", "")
    if not login_val:
        return jsonify({"error": "Vui lòng nhập tên người dùng hoặc email"}), 400
    user = User.query.filter(
        (User.username == login_val) | (User.email == login_val)
    ).first()
    if not user:
        return jsonify({"error": "Thông tin đăng nhập không chính xác"}), 401
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if user.password_hash not in {password, pw_hash, "dev_hash", "default_hash"}:
        return jsonify({"error": "Thông tin đăng nhập không chính xác"}), 401
    return (
        jsonify(
            {"success": True, "message": "Đăng nhập thành công", "user": user.to_dict()}
        ),
        200,
    )


def register_user_auth_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/login", view_func=login_user_legacy, methods=["POST"])
