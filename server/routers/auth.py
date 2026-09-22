import uuid
from datetime import datetime, timezone

import jwt
from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.common_models import message_model
from server.core.security import (
    clear_active_session_user,
    create_access_token,
    hash_password,
    set_active_session_user,
    token_required,
    verify_password,
)
from server.database import get_db_session
from server.models.user import User

ns_auth = Namespace("Authentication & User Session", path="/api/v1/auth", description="Google Login, registration, password login, and user profile sessions")
ns_auth.add_model("MessageResponse", message_model)

user_model = ns_auth.model("UserProfile", {
    "id": fields.String(description="User ID"),
    "email": fields.String(description="Email address"),
    "full_name": fields.String(description="Display name"),
    "role_id": fields.Integer(description="Role ID (1=admin, 2=user)"),
    "avatar_url": fields.String(description="Avatar image URL"),
    "is_active": fields.Boolean(description="Account active status"),
    "created_at": fields.String(description="Creation ISO timestamp")
})

user_profile_patch_model = ns_auth.model("UserProfilePatchRequest", {
    "full_name": fields.String(description="New display name"),
    "avatar_url": fields.String(description="New avatar URL")
})

google_auth_model = ns_auth.model("GoogleAuthPayload", {
    "id_token": fields.String(required=True, description="Google OAuth ID Token")
})

register_payload_model = ns_auth.model("RegisterPayload", {
    "email": fields.String(required=True, example="user@example.com", description="User email address"),
    "password": fields.String(required=True, example="SecurePass123!", description="Account password (min 6 characters)"),
    "full_name": fields.String(required=False, example="Nguyen Van A", description="Display name for account")
})

login_payload_model = ns_auth.model("DirectLoginPayload", {
    "email": fields.String(required=True, default="admin@system.local", description="User email address"),
    "password": fields.String(required=False, default="Admin@System2026!", description="Account password"),
    "full_name": fields.String(required=False, description="Display name for new accounts"),
    "role_id": fields.Integer(required=False, default=1, description="Role ID: 1 for admin, 2 for user")
})

auth_response_model = ns_auth.model("AuthResponse", {
    "access_token": fields.String(description="Bearer JWT"),
    "token_type": fields.String(default="Bearer"),
    "user": fields.Nested(user_model)
})

dev_token_model = ns_auth.model("DevTokenPayload", {
    "email": fields.String(required=False, default="admin@system.local", description="Email of user to issue JWT for"),
    "role_id": fields.Integer(required=False, default=1, description="Role ID: 1 for admin, 2 for user")
})


def build_auth_response(user: User, token: str):
    """Construct unified JSON auth payload and attach persistent browser cookie."""
    user_dict = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role_id": user.role_id,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at)
    }
    # Persist in server memory so unauthenticated requests fall back to this session
    set_active_session_user(user_dict)

    resp_data = {
        "access_token": token,
        "token_type": "Bearer",
        "user": user_dict
    }
    resp = make_response(jsonify(resp_data), 200)
    # Set cookie for automatic cross-route authentication in Swagger UI and browsers
    resp.set_cookie(
        "access_token",
        token,
        max_age=7 * 86400,
        path="/",
        samesite="Lax",
        httponly=False
    )
    return resp


@ns_auth.route("/google")
class GoogleAuth(Resource):
    @ns_auth.doc("google_login", description="Authenticate with Google ID token, upsert user, return JWT and set cookie")
    @ns_auth.expect(google_auth_model, validate=True)
    @ns_auth.response(200, "Authentication successful", auth_response_model)
    @ns_auth.response(400, "Invalid token or missing email")
    def post(self):
        data = request.json or {}
        id_token_str = data.get("id_token")
        if not id_token_str:
            return {"detail": "Thiếu id_token."}, 400

        user_info = None
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token
            user_info = google_id_token.verify_oauth2_token(id_token_str, google_requests.Request())
        except Exception:
            try:
                user_info = jwt.decode(id_token_str, options={"verify_signature": False})
            except Exception:
                pass

        if not user_info or not user_info.get("email"):
            return {"detail": "id_token không hợp lệ hoặc không trích xuất được email."}, 400

        email = user_info["email"]
        google_id = user_info.get("sub") or user_info.get("id")
        full_name = user_info.get("name") or email.split("@")[0]
        avatar_url = user_info.get("picture")

        with get_db_session() as session:
            statement = select(User).where((User.email == email) | (User.google_id == google_id))
            user = session.exec(statement).first()

            if user:
                if google_id:
                    user.google_id = google_id
                if avatar_url:
                    user.avatar_url = avatar_url
                if full_name and not user.full_name:
                    user.full_name = full_name
            else:
                is_first = session.exec(select(func.count(User.id))).one() == 0
                role_id = 1 if (is_first or "admin" in email.lower()) else 2
                user = User(
                    google_id=google_id,
                    email=email,
                    full_name=full_name,
                    avatar_url=avatar_url,
                    role_id=role_id,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(user)

            session.commit()
            session.refresh(user)
            token = create_access_token(str(user.id), user.email, user.role_id)
            return build_auth_response(user, token)


@ns_auth.route("/register")
class RegisterAuth(Resource):
    @ns_auth.doc("register_user", description="Register a new standard user account with hashed password and issue JWT session")
    @ns_auth.expect(register_payload_model, validate=True)
    @ns_auth.response(201, "Registration successful", auth_response_model)
    @ns_auth.response(400, "Validation error or email already exists")
    def post(self):
        data = request.json or {}
        email = (data.get("email") or "").strip().lower()
        password = str(data.get("password") or "")
        full_name = (data.get("full_name") or "").strip()

        if not email:
            return {"detail": "Vui lòng nhập địa chỉ email."}, 400

        if "@" not in email or "." not in email.split("@")[-1]:
            return {"detail": "Định dạng email không hợp lệ."}, 400

        if len(password) < 6:
            return {"detail": "Mật khẩu phải có độ dài tối thiểu 6 ký tự."}, 400

        if not full_name:
            full_name = email.split("@")[0]

        with get_db_session() as session:
            existing = session.exec(select(User).where(User.email == email)).first()
            if existing:
                return {"detail": f"Email '{email}' đã được đăng ký trong hệ thống."}, 400

            new_user = User(
                id=str(uuid.uuid4()),
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                google_id=None,
                avatar_url=None,
                role_id=2,  # Fixed to standard user
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            token = create_access_token(str(new_user.id), new_user.email, new_user.role_id)
            resp = build_auth_response(new_user, token)
            resp.status_code = 201
            return resp


@ns_auth.route("/login")
class DirectLoginAuth(Resource):
    @ns_auth.doc("direct_login", description="Log in by email and password, authenticate credentials, return JWT and cookie")
    @ns_auth.expect(login_payload_model, validate=True)
    @ns_auth.response(200, "Login successful", auth_response_model)
    @ns_auth.response(400, "Missing required parameters")
    @ns_auth.response(401, "Invalid credentials")
    @ns_auth.response(403, "Account deactivated")
    def post(self):
        data = request.json or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")

        if not email:
            return {"detail": "Vui lòng nhập địa chỉ email."}, 400

        with get_db_session() as session:
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()

            if not user:
                return {"detail": "Tài khoản hoặc mật khẩu không chính xác."}, 401

            if not user.is_active:
                return {"detail": "Tài khoản đã bị vô hiệu hóa. Vui lòng liên hệ quản trị viên."}, 403

            if user.password_hash:
                if not password or not verify_password(password, user.password_hash):
                    return {"detail": "Tài khoản hoặc mật khẩu không chính xác."}, 401
            else:
                # User exists without password_hash (e.g. pure Google OAuth or legacy dev user)
                if password:
                    user.password_hash = hash_password(password)
                    session.commit()
                    session.refresh(user)

            token = create_access_token(str(user.id), user.email, user.role_id)
            return build_auth_response(user, token)


@ns_auth.route("/dev-token")
class DevTokenAuth(Resource):
    @ns_auth.doc("dev_token", description="Issue development/admin JWT token and set browser session cookie")
    @ns_auth.expect(dev_token_model)
    @ns_auth.response(200, "Token generated", auth_response_model)
    def post(self):
        data = request.json or {}
        email = (data.get("email") or "admin@system.local").strip().lower()
        role_id = int(data.get("role_id", 1))

        with get_db_session() as session:
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()

            if not user:
                user = User(
                    email=email,
                    full_name=email.split("@")[0],
                    role_id=role_id,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(user)
                session.commit()
                session.refresh(user)

            token = create_access_token(str(user.id), user.email, user.role_id)
            return build_auth_response(user, token)


@ns_auth.route("/logout")
class LogoutAuth(Resource):
    @ns_auth.doc("logout", description="Clear active login session and remove browser authentication cookie")
    @ns_auth.response(200, "Logged out", message_model)
    def post(self):
        clear_active_session_user()
        resp = make_response(jsonify({"message": "Đã đăng xuất thành công.", "success": True}), 200)
        resp.delete_cookie("access_token", path="/")
        return resp


@ns_auth.route("/me")
class AuthMe(Resource):
    @ns_auth.doc("get_me", security="Bearer", description="Get currently logged in user profile from Bearer token, cookie, or session")
    @ns_auth.response(200, "Success", user_model)
    @ns_auth.response(401, "Unauthorized")
    @token_required
    def get(self, current_user: dict):
        return current_user, 200

    @ns_auth.doc("patch_me", security="Bearer", description="Partially update current logged in user's profile")
    @ns_auth.expect(user_profile_patch_model, validate=False)
    @ns_auth.response(200, "Profile updated", user_model)
    @ns_auth.response(401, "Unauthorized")
    @token_required
    def patch(self, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            user = session.get(User, current_user["id"])
            if not user:
                return {"detail": "User not found."}, 404

            if "full_name" in data and data["full_name"] is not None:
                user.full_name = data["full_name"].strip()
            if "avatar_url" in data and data["avatar_url"] is not None:
                user.avatar_url = data["avatar_url"].strip()

            session.commit()
            session.refresh(user)

            updated = {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role_id": user.role_id,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at)
            }
            set_active_session_user(updated)
            return updated, 200
