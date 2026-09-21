import re
import uuid
from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.common_models import count_model, message_model
from server.core.security import admin_required
from server.database import get_db_session
from server.models.category import Category
from server.models.product import Product

ns_categories = Namespace("E-Commerce Categories CRUD", path="/api/v1/categories", description="Full CRUD and product relations for store categories")
ns_categories.add_model("CountResponse", count_model)
ns_categories.add_model("MessageResponse", message_model)

category_model = ns_categories.model("CategoryDetail", {
    "id": fields.String(description="Category UUID"),
    "name": fields.String(description="Category Name"),
    "slug": fields.String(description="SEO URL slug"),
    "description": fields.String(description="Description"),
    "product_count": fields.Integer(description="Number of linked products")
})

category_create_model = ns_categories.model("CategoryCreateRequest", {
    "name": fields.String(required=True, description="Unique category name"),
    "slug": fields.String(required=False, description="Custom slug (auto-generated if omitted)"),
    "description": fields.String(required=False, description="Category description")
})

category_update_model = ns_categories.model("CategoryUpdateRequest", {
    "name": fields.String(required=True, description="Category name"),
    "slug": fields.String(description="Category slug"),
    "description": fields.String(description="Category description")
})

category_patch_model = ns_categories.model("CategoryPatchRequest", {
    "name": fields.String(description="Category name"),
    "slug": fields.String(description="Category slug"),
    "description": fields.String(description="Category description")
})

product_item_model = ns_categories.model("CategoryProductItem", {
    "id": fields.String,
    "name": fields.String,
    "price": fields.Float,
    "stock_quantity": fields.Integer,
    "sku": fields.String,
    "is_available": fields.Boolean
})


def slugify(text: str) -> str:
    """Generate SEO-safe slug from ASCII / Unicode string."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


@ns_categories.route("/count")
class CategoryCount(Resource):
    @ns_categories.doc("count_categories", description="Get total count of product categories")
    @ns_categories.response(200, "Success", count_model)
    def get(self):
        with get_db_session() as session:
            count = session.exec(select(func.count(Category.id))).one()
            return {"count": count}, 200


@ns_categories.route("")
class CategoryListCreate(Resource):
    @ns_categories.doc("list_categories", description="List categories with product counts and search")
    @ns_categories.param("search", "Filter by category name or slug", type=str)
    @ns_categories.param("limit", "Page size", type=int, default=20)
    @ns_categories.param("skip", "Offset", type=int, default=0)
    @ns_categories.response(200, "Success", [category_model])
    def get(self):
        search = request.args.get("search") or request.args.get("q")
        limit = request.args.get("limit", default=20, type=int)
        skip = request.args.get("skip", default=0, type=int)

        with get_db_session() as session:
            stmt = select(Category)
            if search:
                term = f"%{search.strip().lower()}%"
                stmt = stmt.where((func.lower(Category.name).like(term)) | (func.lower(Category.slug).like(term)))
            stmt = stmt.order_by(Category.name.asc()).offset(skip).limit(limit)
            categories = session.exec(stmt).all()

            results = []
            for c in categories:
                p_count = session.exec(select(func.count(Product.id)).where(Product.category_id == c.id)).one()
                results.append({
                    "id": c.id,
                    "name": c.name,
                    "slug": c.slug,
                    "description": c.description,
                    "product_count": p_count
                })
            return results, 200

    @ns_categories.doc("create_category", security="Bearer", description="Create a new product category")
    @ns_categories.expect(category_create_model, validate=True)
    @ns_categories.response(201, "Category created", category_model)
    @ns_categories.response(400, "Duplicate name or slug")
    @admin_required
    def post(self, current_user: dict):
        data = request.json or {}
        name = data.get("name", "").strip()
        if not name:
            return {"detail": "Tên danh mục không được để trống."}, 400

        slug = (data.get("slug") or "").strip() or slugify(name) or str(uuid.uuid4())[:8]
        description = data.get("description", "")

        with get_db_session() as session:
            existing = session.exec(select(Category).where((Category.name == name) | (Category.slug == slug))).first()
            if existing:
                return {"detail": f"Danh mục '{name}' hoặc slug '{slug}' đã tồn tại."}, 400

            category = Category(
                name=name,
                slug=slug,
                description=description
            )
            session.add(category)
            session.commit()
            session.refresh(category)

            return {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "product_count": 0
            }, 201


@ns_categories.route("/<string:category_id>")
class CategoryDetail(Resource):
    @ns_categories.doc("get_category", description="Get category details by ID or slug")
    @ns_categories.response(200, "Success", category_model)
    @ns_categories.response(404, "Category not found")
    def get(self, category_id: str):
        with get_db_session() as session:
            category = session.get(Category, category_id)
            if not category:
                category = session.exec(select(Category).where(Category.slug == category_id)).first()
            if not category:
                return {"detail": f"Category '{category_id}' not found."}, 404

            p_count = session.exec(select(func.count(Product.id)).where(Product.category_id == category.id)).one()
            return {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "product_count": p_count
            }, 200

    @ns_categories.doc("update_category", security="Bearer", description="Full update of category")
    @ns_categories.expect(category_update_model, validate=True)
    @ns_categories.response(200, "Category updated", category_model)
    @ns_categories.response(404, "Category not found")
    @admin_required
    def put(self, category_id: str, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            category = session.get(Category, category_id)
            if not category:
                return {"detail": f"Category ID {category_id} not found."}, 404

            category.name = data.get("name", category.name).strip()
            if "slug" in data and data["slug"]:
                category.slug = data["slug"].strip()
            if "description" in data:
                category.description = data["description"]

            session.commit()
            session.refresh(category)

            p_count = session.exec(select(func.count(Product.id)).where(Product.category_id == category.id)).one()
            return {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "product_count": p_count
            }, 200

    @ns_categories.doc("patch_category", security="Bearer", description="Partial update of category attributes")
    @ns_categories.expect(category_patch_model, validate=False)
    @ns_categories.response(200, "Category patched", category_model)
    @ns_categories.response(404, "Category not found")
    @admin_required
    def patch(self, category_id: str, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            category = session.get(Category, category_id)
            if not category:
                return {"detail": f"Category ID {category_id} not found."}, 404

            if "name" in data and data["name"] is not None:
                category.name = data["name"].strip()
            if "slug" in data and data["slug"] is not None:
                category.slug = data["slug"].strip()
            if "description" in data and data["description"] is not None:
                category.description = data["description"]

            session.commit()
            session.refresh(category)

            p_count = session.exec(select(func.count(Product.id)).where(Product.category_id == category.id)).one()
            return {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "product_count": p_count
            }, 200

    @ns_categories.doc("delete_category", security="Bearer", description="Delete category by ID")
    @ns_categories.response(200, "Category deleted", message_model)
    @ns_categories.response(404, "Category not found")
    @admin_required
    def delete(self, category_id: str, current_user: dict):
        with get_db_session() as session:
            category = session.get(Category, category_id)
            if not category:
                return {"detail": f"Category ID {category_id} not found."}, 404
            session.delete(category)
            session.commit()
            return {"message": f"Category ID {category_id} deleted successfully.", "success": True}, 200


@ns_categories.route("/<string:category_id>/products")
class CategoryProducts(Resource):
    @ns_categories.doc("get_category_products", description="List products belonging to category")
    @ns_categories.response(200, "Success", [product_item_model])
    @ns_categories.response(404, "Category not found")
    def get(self, category_id: str):
        with get_db_session() as session:
            category = session.get(Category, category_id)
            if not category:
                category = session.exec(select(Category).where(Category.slug == category_id)).first()
            if not category:
                return {"detail": f"Category '{category_id}' not found."}, 404

            products = session.exec(select(Product).where(Product.category_id == category.id)).all()
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "stock_quantity": p.stock_quantity,
                    "sku": p.sku,
                    "is_available": p.is_available
                }
                for p in products
            ], 200

