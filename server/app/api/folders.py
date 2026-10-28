"""
folders.py — Folders CRUD API endpoints (Tag: Folders).
Quản lý thực thể: folders (Table 4) theo cấu trúc cây phân cấp.
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.category import Folder

folders_bp = Blueprint("folders", __name__, url_prefix="/api/folders")


@folders_bp.route("", methods=["GET"])
def list_folders():
    """
    Lấy danh sách thư mục cây phân cấp (GET /api/folders)
    ---
    tags:
      - Folders
    summary: Lấy danh sách thư mục (hỗ trợ lọc theo ?user_id=, ?parent_id=, ?category_id=)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID người dùng
      - name: parent_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID thư mục cha (hỗ trợ null cho thư mục gốc)
      - name: category_id
        in: query
        type: integer
        required: false
        description: Lọc theo danh mục
    responses:
      200:
        description: Danh sách thư mục
      500:
        description: Lỗi truy vấn
    """
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
    """
    Tạo thư mục mới (POST /api/folders)
    ---
    tags:
      - Folders
    summary: Tạo thư mục mới (user_id, name, parent_id, category_id, description)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
              description: ID người dùng sở hữu thư mục
            name:
              type: string
              example: "Chương 1 - Cơ Bản"
              description: Tên thư mục
            parent_id:
              type: integer
              example: null
              description: ID thư mục cha (nếu là thư mục con)
            category_id:
              type: integer
              example: 1
              description: ID danh mục liên kết
            description:
              type: string
              example: "Thư mục chứa các bộ thẻ kiến thức nền tảng"
    responses:
      201:
        description: Tạo thư mục thành công
      400:
        description: Thiếu trường bắt buộc name hoặc user_id
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    user_id = data.get("user_id")

    if not name or not str(name).strip():
        return jsonify({"error": "Trường 'name' là bắt buộc"}), 400
    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400

    folder = Folder(
        name=str(name).strip(),
        user_id=int(user_id),
        category_id=data.get("category_id"),
        parent_id=data.get("parent_id"),
        description=data.get("description"),
    )
    try:
        db.session.add(folder)
        db.session.commit()
        return jsonify(folder.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo thư mục: {str(exc)}"}), 500


@folders_bp.route("/<int:folder_id>", methods=["GET"])
def get_folder_by_id(folder_id: int):
    """
    Xem chi tiết thư mục kèm thư mục con và bộ thẻ bên trong (GET /api/folders/{id})
    ---
    tags:
      - Folders
    summary: Chi tiết thư mục kèm danh sách folder con và deck bên trong
    parameters:
      - name: folder_id
        in: path
        type: integer
        required: true
        description: ID thư mục
    responses:
      200:
        description: Chi tiết thư mục kèm subfolders và decks
      404:
        description: Không tìm thấy thư mục
    """
    folder = db.session.get(Folder, folder_id)
    if not folder:
        return jsonify({"error": f"Không tìm thấy thư mục ID {folder_id}"}), 404

    folder_dict = folder.to_dict()
    subfolders: Any = getattr(folder, "children", [])
    folder_decks: Any = getattr(folder, "decks", [])
    folder_dict["subfolders"] = [f.to_dict() for f in subfolders] if subfolders else []
    folder_dict["decks"] = [d.to_dict() for d in folder_decks] if folder_decks else []
    return jsonify(folder_dict), 200


@folders_bp.route("/<int:folder_id>", methods=["PUT"])
def update_folder_by_id(folder_id: int):
    """
    Cập nhật thư mục (PUT /api/folders/{id})
    ---
    tags:
      - Folders
    summary: Cập nhật thư mục (đổi tên, chuyển parent_id hoặc category_id)
    parameters:
      - name: folder_id
        in: path
        type: integer
        required: true
        description: ID thư mục
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "Chương 1 - Nhập Môn Cập Nhật"
            parent_id:
              type: integer
              example: null
            category_id:
              type: integer
              example: 2
            description:
              type: string
              example: "Nội dung cập nhật"
    responses:
      200:
        description: Cập nhật thư mục thành công
      404:
        description: Không tìm thấy thư mục
      500:
        description: Lỗi máy chủ
    """
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
        # Chống đệ quy vòng lặp chính nó
        new_parent = data["parent_id"]
        if new_parent == folder_id:
            return jsonify({"error": "Một thư mục không thể là cha của chính nó"}), 400
        folder.parent_id = new_parent

    try:
        db.session.commit()
        return jsonify(folder.to_dict()), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật thư mục: {str(exc)}"}), 500


@folders_bp.route("/<int:folder_id>", methods=["DELETE"])
def delete_folder_by_id(folder_id: int):
    """
    Xóa thư mục đệ quy theo ON DELETE CASCADE (DELETE /api/folders/{id})
    ---
    tags:
      - Folders
    summary: Xóa thư mục (xóa đệ quy các thư mục con theo ON DELETE CASCADE)
    parameters:
      - name: folder_id
        in: path
        type: integer
        required: true
        description: ID thư mục cần xóa
    responses:
      200:
        description: Đã xóa thư mục và các thư mục con thành công
      404:
        description: Không tìm thấy thư mục
      500:
        description: Lỗi xóa thư mục
    """
    folder = db.session.get(Folder, folder_id)
    if not folder:
        return jsonify({"error": f"Không tìm thấy thư mục ID {folder_id}"}), 404

    try:
        db.session.delete(folder)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Đã xóa thư mục ID {folder_id} và các thư mục con thành công"
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa thư mục: {str(exc)}"}), 500
