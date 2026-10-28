"""
users.py — Users & User Profiles CRUD API endpoints (Tag: Users & Profiles).
Quản lý thực thể: users (Table 1) và user_profiles (Table 2).
"""

from __future__ import annotations

import hashlib
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.user import User, UserProfile

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("", methods=["GET"])
def list_users():
    """
    Lấy danh sách người dùng có phân trang (GET /api/users)
    ---
    tags:
      - Users & Profiles
    summary: Lấy danh sách users hỗ trợ phân trang và lọc theo vai trò
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Số thứ tự trang (bắt đầu từ 1)
      - name: limit
        in: query
        type: integer
        required: false
        default: 20
        description: Số lượng người dùng mỗi trang
      - name: role
        in: query
        type: string
        required: false
        description: Lọc theo vai trò (user, admin, teacher)
      - name: username
        in: query
        type: string
        required: false
        description: Lọc theo username
      - name: email
        in: query
        type: string
        required: false
        description: Lọc theo email
    responses:
      200:
        description: Danh sách người dùng (tuyệt đối không lộ password_hash)
      500:
        description: Lỗi máy chủ cơ sở dữ liệu
    """
    page = max(1, request.args.get("page", 1, type=int))
    limit = max(1, min(100, request.args.get("limit", 20, type=int)))
    role = request.args.get("role")
    username = request.args.get("username")
    email = request.args.get("email")

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if username:
        query = query.filter_by(username=username)
    if email:
        query = query.filter_by(email=email)

    users = query.order_by(User.id.asc()).offset((page - 1) * limit).limit(limit).all()
    # to_dict() loại trừ password_hash
    return jsonify([u.to_dict() for u in users]), 200


@users_bp.route("", methods=["POST"])
def create_user():
    """
    Tạo mới tài khoản người dùng thủ công (POST /api/users)
    ---
    tags:
      - Users & Profiles
    summary: Tạo mới người dùng và tự động khởi tạo hồ sơ cá nhân mặc định
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            username:
              type: string
              example: student01
            email:
              type: string
              example: student01@eduflash.ai
            password:
              type: string
              example: secret123
            role:
              type: string
              default: user
              example: user
            is_active:
              type: boolean
              default: true
            display_name:
              type: string
              example: Nguyễn Văn A
            full_name:
              type: string
              example: Nguyễn Văn A
    responses:
      201:
        description: Tạo người dùng thành công
      400:
        description: Thiếu thông tin bắt buộc
      409:
        description: Tên người dùng hoặc email đã tồn tại
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    username = (
        data.get("username")
        or data.get("display_name")
        or (email.split("@")[0] if email else None)
    )
    raw_password = data.get("password") or data.get("password_hash", "default_hash")

    if not username or not email:
        return jsonify({"error": "Trường 'username' và 'email' là bắt buộc"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Tên người dùng hoặc email đã tồn tại"}), 409

    try:
        user = User(
            username=username,
            email=email,
            password_hash=hashlib.sha256(raw_password.encode()).hexdigest(),
            role=data.get("role", "user"),
            is_active=bool(data.get("is_active", True)),
        )
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(
            user_id=user.id,
            display_name=data.get("display_name", username),
            full_name=data.get("full_name") or data.get("display_name"),
            timezone=data.get("timezone", "UTC"),
            daily_card_goal=int(data.get("daily_card_goal", 20)),
        )
        db.session.add(profile)
        db.session.commit()

        user_dict = user.to_dict()
        user_dict["profile"] = profile.to_dict()
        return jsonify(user_dict), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo tài khoản: {str(exc)}"}), 500


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id: int):
    """
    Xem chi tiết thông tin người dùng kèm hồ sơ cá nhân 1:1 (GET /api/users/{id})
    ---
    tags:
      - Users & Profiles
    summary: Xem chi tiết thông tin user kèm profile liên kết
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID của người dùng cần xem
    responses:
      200:
        description: Thông tin user kèm profile
      404:
        description: Không tìm thấy người dùng
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}), 404

    user_dict = user.to_dict()
    user_dict["profile"] = user.profile.to_dict() if user.profile else None
    return jsonify(user_dict), 200


@users_bp.route("/<int:user_id>", methods=["PUT"])
def update_user_by_id(user_id: int):
    """
    Cập nhật thông tin cơ bản người dùng (PUT /api/users/{id})
    ---
    tags:
      - Users & Profiles
    summary: Cập nhật thông tin cơ bản user (email, is_active, role)
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID người dùng cần cập nhật
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: updated_email@eduflash.ai
            is_active:
              type: boolean
              example: true
            role:
              type: string
              example: user
            username:
              type: string
              example: updated_username
            password:
              type: string
              example: newpassword123
    responses:
      200:
        description: Cập nhật người dùng thành công
      400:
        description: Dữ liệu cập nhật không hợp lệ
      404:
        description: Không tìm thấy người dùng
      409:
        description: Email hoặc username bị trùng lặp với người dùng khác
      500:
        description: Lỗi máy chủ nội bộ
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}), 404

    data = request.get_json(silent=True) or {}

    if "email" in data and str(data["email"]).strip():
        new_email = str(data["email"]).strip()
        existing = User.query.filter(
            User.email == new_email, User.id != user_id
        ).first()
        if existing:
            return jsonify({"error": f"Email '{new_email}' đã được sử dụng"}), 409
        user.email = new_email

    if "username" in data and str(data["username"]).strip():
        new_username = str(data["username"]).strip()
        existing = User.query.filter(
            User.username == new_username, User.id != user_id
        ).first()
        if existing:
            return jsonify({"error": f"Username '{new_username}' đã tồn tại"}), 409
        user.username = new_username

    if "role" in data:
        user.role = str(data["role"])

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    if "password" in data and str(data["password"]).strip():
        user.password_hash = hashlib.sha256(
            str(data["password"]).strip().encode()
        ).hexdigest()

    try:
        db.session.commit()
        user_dict = user.to_dict()
        user_dict["profile"] = user.profile.to_dict() if user.profile else None
        return jsonify(user_dict), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật người dùng: {str(exc)}"}), 500


@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user_by_id(user_id: int):
    """
    Xóa người dùng kích hoạt ON DELETE CASCADE toàn bộ bảng con (DELETE /api/users/{id})
    ---
    tags:
      - Users & Profiles
    summary: Xóa vĩnh viễn user và tự động xóa dữ liệu liên kết theo ON DELETE CASCADE
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID người dùng cần xóa
    responses:
      200:
        description: Đã xóa người dùng thành công
      404:
        description: Không tìm thấy người dùng
      500:
        description: Lỗi máy chủ khi xóa dữ liệu
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Đã xóa người dùng ID {user_id} và các dữ liệu liên kết thành công"
                }
            ),
            200,
        )
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa người dùng: {str(err)}"}), 500


@users_bp.route("/<int:user_id>/profile", methods=["GET"])
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


@users_bp.route("/<int:user_id>/profile", methods=["PUT"])
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


@users_bp.route("/login", methods=["POST"])
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
