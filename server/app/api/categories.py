"""
categories.py — Categories CRUD API endpoints (Tag: Categories).
Quản lý thực thể: categories (Table 3).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.category import Category
from app.models.user import User

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.route("", methods=["GET"])
def list_categories():
    """
    Lấy danh sách các danh mục phân loại (GET /api/categories)
    ---
    tags:
      - Categories
    summary: Lấy danh sách danh mục (hỗ trợ lọc ?user_id=)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc danh mục theo ID người dùng
    responses:
      200:
        description: Danh sách danh mục
      500:
        description: Lỗi truy vấn cơ sở dữ liệu
    """
    user_id = request.args.get("user_id", type=int)
    query = Category.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    categories = query.order_by(Category.id.asc()).all()
    return jsonify([c.to_dict() for c in categories]), 200


@categories_bp.route("", methods=["POST"])
def create_category():
    """
    Tạo danh mục mới (POST /api/categories)
    ---
    tags:
      - Categories
    summary: Tạo danh mục mới (user_id, name, description, color_code)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            user_id:
              type: integer
              example: 1
              description: ID người dùng sở hữu danh mục
            name:
              type: string
              example: "Lập trình Web"
              description: Tên danh mục
            description:
              type: string
              example: "Các tài liệu và bộ thẻ liên quan đến phát triển web"
              description: Mô tả chi tiết
            color_code:
              type: string
              example: "#3B82F6"
              description: Mã màu đại diện định dạng HEX (#RRGGBB)
    responses:
      201:
        description: Tạo danh mục thành công
      400:
        description: Tên danh mục để trống hoặc không hợp lệ
      500:
        description: Lỗi lưu trữ cơ sở dữ liệu
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name or not str(name).strip():
        return jsonify({"error": "Trường 'name' là bắt buộc"}), 400

    user_id = data.get("user_id")
    if user_id is not None:
        try:
            user_id = int(user_id)
            if not db.session.get(User, user_id):
                return (
                    jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}),
                    404,
                )
        except (ValueError, TypeError):
            return jsonify({"error": "Trường 'user_id' phải là số nguyên"}), 400

    category = Category(
        name=str(name).strip(),
        description=data.get("description"),
        color_code=data.get("color_code", "#3B82F6"),
        user_id=user_id,
    )
    try:
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo danh mục: {str(exc)}"}), 500


@categories_bp.route("/<int:cat_id>", methods=["GET"])
def get_category_by_id(cat_id: int):
    """
    Xem chi tiết danh mục (GET /api/categories/{id})
    ---
    tags:
      - Categories
    summary: Xem thông tin chi tiết một danh mục
    parameters:
      - name: cat_id
        in: path
        type: integer
        required: true
        description: ID danh mục
    responses:
      200:
        description: Chi tiết danh mục
      404:
        description: Không tìm thấy danh mục
    """
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": f"Không tìm thấy danh mục ID {cat_id}"}), 404
    return jsonify(cat.to_dict()), 200


@categories_bp.route("/<int:cat_id>", methods=["PUT"])
def update_category_by_id(cat_id: int):
    """
    Cập nhật danh mục (PUT /api/categories/{id})
    ---
    tags:
      - Categories
    summary: Cập nhật tên, mô tả, màu sắc (color_code)
    parameters:
      - name: cat_id
        in: path
        type: integer
        required: true
        description: ID danh mục
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "Lập trình Web Nâng Cao"
            description:
              type: string
              example: "Bộ kiến trúc Web Fullstack"
            color_code:
              type: string
              example: "#10B981"
    responses:
      200:
        description: Cập nhật thành công
      404:
        description: Không tìm thấy danh mục
      500:
        description: Lỗi máy chủ
    """
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": f"Không tìm thấy danh mục ID {cat_id}"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data and str(data["name"]).strip():
        cat.name = str(data["name"]).strip()
    if "description" in data:
        cat.description = data["description"]
    if "color_code" in data:
        cat.color_code = data["color_code"]

    try:
        db.session.commit()
        return jsonify(cat.to_dict()), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật danh mục: {str(exc)}"}), 500


@categories_bp.route("/<int:cat_id>", methods=["DELETE"])
def delete_category_by_id(cat_id: int):
    """
    Xóa danh mục theo ID kích hoạt ON DELETE CASCADE (DELETE /api/categories/{id})
    ---
    tags:
      - Categories
    summary: Xóa danh mục (kích hoạt ON DELETE CASCADE)
    parameters:
      - name: cat_id
        in: path
        type: integer
        required: true
        description: ID danh mục cần xóa
    responses:
      200:
        description: Đã xóa danh mục thành công
      404:
        description: Không tìm thấy danh mục
      500:
        description: Lỗi xóa danh mục
    """
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": f"Không tìm thấy danh mục ID {cat_id}"}), 404

    try:
        db.session.delete(cat)
        db.session.commit()
        return jsonify({"message": f"Đã xóa danh mục ID {cat_id} thành công"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa danh mục: {str(exc)}"}), 500
