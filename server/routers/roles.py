from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.common_models import count_model, message_model
from server.core.security import admin_required
from server.database import get_db_session
from server.models.role import Role
from server.models.user import User

ns_roles = Namespace("System Roles CRUD", path="/api/v1/roles", description="Full CRUD for system roles")
ns_roles.add_model("CountResponse", count_model)
ns_roles.add_model("MessageResponse", message_model)

role_create_model = ns_roles.model("RoleCreateRequest", {
    "name": fields.String(required=True, description="Unique role name (e.g. admin, user, manager)"),
    "description": fields.String(description="Role description")
})

role_update_model = ns_roles.model("RoleUpdateRequest", {
    "name": fields.String(description="Role name"),
    "description": fields.String(description="Role description")
})

role_patch_model = ns_roles.model("RolePatchRequest", {
    "name": fields.String(description="Role name"),
    "description": fields.String(description="Role description")
})

role_model = ns_roles.model("Role", {
    "id": fields.Integer(description="Role ID"),
    "name": fields.String(description="Role identifier"),
    "description": fields.String(description="Description")
})

user_role_item_model = ns_roles.model("RoleAssignedUser", {
    "id": fields.String,
    "email": fields.String,
    "full_name": fields.String,
    "is_active": fields.Boolean
})


@ns_roles.route("/count")
class RoleCount(Resource):
    @ns_roles.doc("count_roles", description="Count system roles")
    @ns_roles.response(200, "Success", count_model)
    def get(self):
        with get_db_session() as session:
            count = session.exec(select(func.count(Role.id))).one()
            return {"count": count}, 200


@ns_roles.route("")
class RoleListCreate(Resource):
    @ns_roles.doc("list_roles", description="List all system roles")
    @ns_roles.response(200, "Success", [role_model])
    def get(self):
        with get_db_session() as session:
            roles = session.exec(select(Role).order_by(Role.id.asc())).all()
            return [{"id": r.id, "name": r.name, "description": r.description} for r in roles], 200

    @ns_roles.doc("create_role", security="Bearer", description="Create a new system role")
    @ns_roles.expect(role_create_model, validate=True)
    @ns_roles.response(201, "Role created", role_model)
    @ns_roles.response(400, "Duplicate role name")
    @admin_required
    def post(self, current_user: dict):
        data = request.json or {}
        name = data.get("name", "").strip()
        description = data.get("description", "")
        if not name:
            return {"detail": "Tên role không được để trống."}, 400

        with get_db_session() as session:
            exists = session.exec(select(Role).where(Role.name == name)).first()
            if exists:
                return {"detail": f"Role '{name}' đã tồn tại."}, 400
            new_role = Role(name=name, description=description)
            session.add(new_role)
            session.commit()
            session.refresh(new_role)
            return {"id": new_role.id, "name": new_role.name, "description": new_role.description}, 201


@ns_roles.route("/<int:role_id>")
class RoleDetail(Resource):
    @ns_roles.doc("get_role", description="Get role details by ID")
    @ns_roles.response(200, "Success", role_model)
    @ns_roles.response(404, "Role not found")
    def get(self, role_id: int):
        with get_db_session() as session:
            role = session.get(Role, role_id)
            if not role:
                return {"detail": f"Role ID {role_id} not found."}, 404
            return {"id": role.id, "name": role.name, "description": role.description}, 200

    @ns_roles.doc("update_role", security="Bearer", description="Update existing role")
    @ns_roles.expect(role_update_model, validate=True)
    @ns_roles.response(200, "Role updated", role_model)
    @ns_roles.response(404, "Role not found")
    @admin_required
    def put(self, role_id: int, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            role = session.get(Role, role_id)
            if not role:
                return {"detail": f"Role ID {role_id} not found."}, 404
            if "name" in data and data["name"]:
                role.name = data["name"].strip()
            if "description" in data and data["description"] is not None:
                role.description = data["description"]
            session.commit()
            session.refresh(role)
            return {"id": role.id, "name": role.name, "description": role.description}, 200

    @ns_roles.doc("patch_role", security="Bearer", description="Partially update existing role")
    @ns_roles.expect(role_patch_model, validate=False)
    @ns_roles.response(200, "Role updated", role_model)
    @ns_roles.response(404, "Role not found")
    @admin_required
    def patch(self, role_id: int, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            role = session.get(Role, role_id)
            if not role:
                return {"detail": f"Role ID {role_id} not found."}, 404
            if "name" in data and data["name"] is not None:
                role.name = data["name"].strip()
            if "description" in data and data["description"] is not None:
                role.description = data["description"]
            session.commit()
            session.refresh(role)
            return {"id": role.id, "name": role.name, "description": role.description}, 200

    @ns_roles.doc("delete_role", security="Bearer", description="Delete role by ID")
    @ns_roles.response(200, "Role deleted", message_model)
    @ns_roles.response(400, "Cannot delete protected system role")
    @ns_roles.response(404, "Role not found")
    @admin_required
    def delete(self, role_id: int, current_user: dict):
        if role_id in (1, 2):
            return {"detail": "Không thể xóa role hệ thống mặc định (admin/user)."}, 400
        with get_db_session() as session:
            role = session.get(Role, role_id)
            if not role:
                return {"detail": f"Role ID {role_id} not found."}, 404
            session.delete(role)
            session.commit()
            return {"message": f"Role ID {role_id} deleted successfully.", "success": True}, 200


@ns_roles.route("/<int:role_id>/users")
class RoleUsersResource(Resource):
    @ns_roles.doc("list_role_users", description="List user accounts assigned to a specific role")
    @ns_roles.response(200, "Success", [user_role_item_model])
    @ns_roles.response(404, "Role not found")
    def get(self, role_id: int):
        with get_db_session() as session:
            role = session.get(Role, role_id)
            if not role:
                return {"detail": f"Role ID {role_id} not found."}, 404

            users = session.exec(select(User).where(User.role_id == role_id)).all()
            return [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "full_name": u.full_name,
                    "is_active": u.is_active
                }
                for u in users
            ], 200
