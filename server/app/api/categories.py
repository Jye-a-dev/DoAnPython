"""
categories.py — Categories CRUD API endpoints (Table 3: categories).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.category import Category

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.route("", methods=["GET"])
def list_categories():
    """Lấy danh sách các danh mục phân loại"""
    user_id = request.args.get("user_id", type=int)
    query = Category.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    categories = query.order_by(Category.id.asc()).all()
    return jsonify([c.to_dict() for c in categories]), 200


@categories_bp.route("", methods=["POST"])
def create_category():
    """Tạo mới danh mục phân loại"""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name or not str(name).strip():
        return jsonify({"error": "Trường 'name' là bắt buộc"}), 400
    category = Category(
        name=str(name).strip(),
        description=data.get("description"),
        color_code=data.get("color_code", "#3B82F6"),
        user_id=data.get("user_id"),
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@categories_bp.route("/<int:cat_id>", methods=["GET"])
def get_category_by_id(cat_id: int):
    """Lấy thông tin chi tiết một danh mục"""
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": f"Không tìm thấy danh mục ID {cat_id}"}), 404
    return jsonify(cat.to_dict()), 200


@categories_bp.route("/<int:cat_id>", methods=["PUT"])
def update_category_by_id(cat_id: int):
    """Cập nhật thông tin danh mục"""
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
    db.session.commit()
    return jsonify(cat.to_dict()), 200


@categories_bp.route("/<int:cat_id>", methods=["DELETE"])
def delete_category_by_id(cat_id: int):
    """Xóa danh mục phân loại"""
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": f"Không tìm thấy danh mục ID {cat_id}"}), 404
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": f"Đã xóa danh mục ID {cat_id} thành công"}), 200
