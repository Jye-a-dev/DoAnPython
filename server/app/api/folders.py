"""
folders.py — Folders CRUD API endpoints (Table 4: folders).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.category import Folder

folders_bp = Blueprint("folders", __name__, url_prefix="/api/folders")


@folders_bp.route("", methods=["GET"])
def list_folders():
    """Lấy danh sách thư mục bài học (hỗ trợ phân cấp)"""
    user_id = request.args.get("user_id", type=int)
    category_id = request.args.get("category_id", type=int)
    parent_id = request.args.get("parent_id", type=int)
    query = Folder.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if category_id is not None:
        query = query.filter_by(category_id=category_id)
    if parent_id is not None:
        query = query.filter_by(parent_id=parent_id)
    folders = query.order_by(Folder.id.asc()).all()
    return jsonify([f.to_dict() for f in folders]), 200


@folders_bp.route("", methods=["POST"])
def create_folder():
    """Tạo mới thư mục bài học"""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    user_id = data.get("user_id")
    if not name or not str(name).strip():
        return jsonify({"error": "Trường 'name' là bắt buộc"}), 400
    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400
    folder = Folder(
        name=str(name).strip(),
        user_id=user_id,
        category_id=data.get("category_id"),
        parent_id=data.get("parent_id"),
        description=data.get("description"),
    )
    db.session.add(folder)
    db.session.commit()
    return jsonify(folder.to_dict()), 201


@folders_bp.route("/<int:folder_id>", methods=["GET"])
def get_folder_by_id(folder_id: int):
    """Lấy thông tin chi tiết một thư mục"""
    folder = db.session.get(Folder, folder_id)
    if not folder:
        return jsonify({"error": f"Không tìm thấy thư mục ID {folder_id}"}), 404
    return jsonify(folder.to_dict()), 200


@folders_bp.route("/<int:folder_id>", methods=["PUT"])
def update_folder_by_id(folder_id: int):
    """Cập nhật thông tin thư mục"""
    folder = db.session.get(Folder, folder_id)
    if not folder:
        return jsonify({"error": f"Không tìm thấy thư mục ID {folder_id}"}), 404
    data = request.get_json(silent=True) or {}
    if "name" in data and str(data["name"]).strip():
        folder.name = str(data["name"]).strip()
    if "description" in data:
        folder.description = data["description"]
    if "category_id" in data:
        folder.category_id = data["category_id"]
    if "parent_id" in data:
        folder.parent_id = data["parent_id"]
    db.session.commit()
    return jsonify(folder.to_dict()), 200


@folders_bp.route("/<int:folder_id>", methods=["DELETE"])
def delete_folder_by_id(folder_id: int):
    """Xóa thư mục bài học"""
    folder = db.session.get(Folder, folder_id)
    if not folder:
        return jsonify({"error": f"Không tìm thấy thư mục ID {folder_id}"}), 404
    db.session.delete(folder)
    db.session.commit()
    return jsonify({"message": f"Đã xóa thư mục ID {folder_id} thành công"}), 200
