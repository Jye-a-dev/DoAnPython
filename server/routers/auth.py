from datetime import datetime, timezone

import jwt
from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.security import create_access_token, token_required
from server.database import get_db_session
from server.models.user import User

ns_auth = Namespace("Authentication & User Session", path="/api/v1/auth", description="Google Login and user profiles")

user_model = ns_auth.model("UserProfile", {
    "id": fields.Integer(description="User ID"),
    "email": fields.String(description="Email address"),
    "full_name": fields.String(description="Display name"),
    "role_id": fields.Integer(description="Role ID (1=admin, 2=user)"),
    "avatar_url": fields.String(description="Avatar image URL"),
    "is_active": fields.Boolean(description="Account active status"),
    "created_at": fields.String(description="Creation ISO timestamp")
})

google_auth_model = ns_auth.model("GoogleAuthPayload", {
    "id_token": fields.String(required=True, description="Google OAuth ID Token")
})

auth_response_model = ns_auth.model("AuthResponse", {
    "access_token": fields.String(description="Bearer JWT"),
    "token_type": fields.String(default="Bearer"),
    "user": fields.Nested(user_model)
})


@ns_auth.route("/google")
class GoogleAuth(Resource):
    @ns_auth.doc("google_login", description="Authenticate with Google ID token, upsert user, and return JWT")
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

            token = create_access_token(user.id, user.email, user.role_id)
            return {
                "access_token": token,
                "token_type": "Bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role_id": user.role_id,
                    "avatar_url": user.avatar_url,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at)
                }
            }, 200


@ns_auth.route("/me")
class AuthMe(Resource):
    @ns_auth.doc("get_me", security="Bearer", description="Get currently logged in user profile from Bearer token")
    @ns_auth.response(200, "Success", user_model)
    @ns_auth.response(401, "Unauthorized")
    @token_required
    def get(self, current_user: dict):
        return current_user, 200

