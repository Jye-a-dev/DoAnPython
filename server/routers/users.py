from datetime import datetime, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.common_models import count_model, message_model
from server.core.security import admin_required
from server.database import get_db_session
from server.models.user import User

ns_users = Namespace("System Users CRUD", path="/api/v1/users", description="Full CRUD for user accounts and RBAC")
ns_users.add_model("CountResponse", count_model)
ns_users.add_model("MessageResponse", message_model)

user_model = ns_users.model("UserAccount", {
    "id": fields.Integer(description="User ID"),
    "email": fields.String(description="Email address"),
    "full_name": fields.String(description="Display name"),
    "role_id": fields.Integer(description="Role ID (1=admin, 2=user)"),
    "avatar_url": fields.String(description="Avatar image URL"),
    "is_active": fields.Boolean(description="Account active status"),
    "created_at": fields.String(description="Creation ISO timestamp")
})

user_create_model = ns_users.model("UserCreateRequest", {
    "email": fields.String(required=True, description="Email address"),
    "full_name": fields.String(description="Full name"),
    "role_id": fields.Integer(default=2, description="Role ID (1=admin, 2=user)"),
    "avatar_url": fields.String(description="Avatar URL"),
    "is_active": fields.Boolean(default=True, description="Account active state")
})

user_update_model = ns_users.model("UserUpdateRequest", {
    "email": fields.String(description="Email address"),
    "full_name": fields.String(description="Full name"),
    "is_active": fields.Boolean(description="Account active state"),
    "role_id": fields.Integer(description="Role ID")
})


@ns_users.route("/count")
class UserCount(Resource):
    @ns_users.doc("count_users", description="Count users with optional filters")
    @ns_users.param("role_id", "Filter by role ID", type=int)
    @ns_users.param("is_active", "Filter by active state", type=bool)
    @ns_users.response(200, "Success", count_model)
    def get(self):
        role_id = request.args.get("role_id", type=int)
        is_active_raw = request.args.get("is_active")

        with get_db_session() as session:
            stmt = select(func.count(User.id))
            if role_id is not None:
                stmt = stmt.where(User.role_id == role_id)
            if is_active_raw is not None:
                is_active = is_active_raw.lower() in ("true", "1", "t")
                stmt = stmt.where(User.is_active == is_active)
            count = session.exec(stmt).one()
            return {"count": count}, 200


@ns_users.route("")
class UserListCreate(Resource):
    @ns_users.doc("list_users", description="Retrieve paginated user accounts")
    @ns_users.param("limit", "Number of users", type=int, default=10)
    @ns_users.param("skip", "Offset", type=int, default=0)
    @ns_users.response(200, "Success", [user_model])
    def get(self):
        limit = request.args.get("limit", default=10, type=int)
        skip = request.args.get("skip", default=0, type=int)

        with get_db_session() as session:
            users = session.exec(select(User).order_by(User.id.asc()).offset(skip).limit(limit)).all()
            return [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "role_id": u.role_id,
                    "avatar_url": u.avatar_url,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if hasattr(u.created_at, "isoformat") else str(u.created_at)
                } for u in users
            ], 200

    @ns_users.doc("create_user", security="Bearer", description="Manually register a new user account")
    @ns_users.expect(user_create_model, validate=True)
    @ns_users.response(201, "User created", user_model)
    @ns_users.response(400, "Email already registered")
    @admin_required
    def post(self, current_user: dict):
        data = request.json or {}
        email = data.get("email", "").strip()
        if not email:
            return {"detail": "Email là bắt buộc."}, 400

        with get_db_session() as session:
            exists = session.exec(select(User).where(User.email == email)).first()
            if exists:
                return {"detail": f"User với email '{email}' đã tồn tại."}, 400

            new_user = User(
                email=email,
                full_name=data.get("full_name"),
                role_id=int(data.get("role_id", 2)),
                avatar_url=data.get("avatar_url"),
                is_active=bool(data.get("is_active", True)),
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            return {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role_id": new_user.role_id,
                "avatar_url": new_user.avatar_url,
                "is_active": new_user.is_active,
                "created_at": new_user.created_at.isoformat() if hasattr(new_user.created_at, "isoformat") else str(new_user.created_at)
            }, 201


@ns_users.route("/<int:user_id>")
class UserDetail(Resource):
    @ns_users.doc("get_user", description="Get user details by ID")
    @ns_users.response(200, "Success", user_model)
    @ns_users.response(404, "User not found")
    def get(self, user_id: int):
        with get_db_session() as session:
            user = session.get(User, user_id)
            if not user:
                return {"detail": f"User ID {user_id} not found."}, 404
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role_id": user.role_id,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at)
            }, 200

    @ns_users.doc("update_user", security="Bearer", description="Update user active state or role")
    @ns_users.expect(user_update_model, validate=True)
    @ns_users.response(200, "User updated", user_model)
    @ns_users.response(404, "User not found")
    @admin_required
    def put(self, user_id: int, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            user = session.get(User, user_id)
            if not user:
                return {"detail": f"User ID {user_id} not found."}, 404

            if "email" in data and data["email"]:
                user.email = data["email"].strip()
            if "full_name" in data and data["full_name"] is not None:
                user.full_name = data["full_name"]
            if "is_active" in data and data["is_active"] is not None:
                user.is_active = bool(data["is_active"])
            if "role_id" in data and data["role_id"] is not None:
                user.role_id = int(data["role_id"])

            session.commit()
            session.refresh(user)

            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role_id": user.role_id,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at)
            }, 200

    @ns_users.doc("delete_user", security="Bearer", description="Delete user account by ID")
    @ns_users.response(200, "User deleted", message_model)
    @ns_users.response(400, "Cannot delete current authenticated user")
    @ns_users.response(404, "User not found")
    @admin_required
    def delete(self, user_id: int, current_user: dict):
        if user_id == current_user["id"]:
            return {"detail": "Không thể tự xóa tài khoản đang đăng nhập."}, 400
        with get_db_session() as session:
            user = session.get(User, user_id)
            if not user:
                return {"detail": f"User ID {user_id} not found."}, 404
            session.delete(user)
            session.commit()
            return {"message": f"User ID {user_id} deleted successfully.", "success": True}, 200
