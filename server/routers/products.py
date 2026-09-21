import json
from datetime import datetime, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.common_models import count_model, message_model
from server.core.security import admin_required
from server.database import get_db_session
from server.models.ocr_record import OCRRecord
from server.models.product import Product

ns_products = Namespace("E-Commerce Products & Visual Search", path="/api/v1/products", description="Products catalog and camera-to-shop visual search")
ns_products.add_model("CountResponse", count_model)
ns_products.add_model("MessageResponse", message_model)

product_model = ns_products.model("ProductDetail", {
    "id": fields.String,
    "category_id": fields.String,
    "name": fields.String,
    "class_name": fields.String,
    "sku": fields.String,
    "price": fields.Float,
    "stock_quantity": fields.Integer,
    "image_url": fields.String,
    "description": fields.String,
    "is_available": fields.Boolean,
    "created_at": fields.String
})

product_create_model = ns_products.model("ProductCreateRequest", {
    "name": fields.String(required=True, description="Product title"),
    "category_id": fields.String(description="Category ID"),
    "class_name": fields.String(description="COCO/YOLO label (e.g. laptop, bottle, apple)"),
    "sku": fields.String(description="SKU Code"),
    "price": fields.Float(required=True, min=0.0, description="Price in VND"),
    "stock_quantity": fields.Integer(default=0, min=0, description="Stock quantity"),
    "image_url": fields.String(description="Product photo URL"),
    "description": fields.String(description="Product description"),
    "is_available": fields.Boolean(default=True, description="Availability flag")
})

product_update_model = ns_products.model("ProductUpdateRequest", {
    "name": fields.String(description="Product title"),
    "category_id": fields.String(description="Category ID"),
    "class_name": fields.String(description="COCO/YOLO label (e.g. laptop, bottle, apple)"),
    "sku": fields.String(description="SKU Code"),
    "price": fields.Float(min=0.0, description="Price in VND"),
    "stock_quantity": fields.Integer(min=0, description="Stock quantity"),
    "image_url": fields.String(description="Product photo URL"),
    "description": fields.String(description="Product description"),
    "is_available": fields.Boolean(description="Availability flag")
})

product_patch_model = ns_products.model("ProductPatchRequest", {
    "name": fields.String(description="Product title"),
    "category_id": fields.String(description="Category ID"),
    "class_name": fields.String(description="COCO/YOLO label (e.g. laptop, bottle, apple)"),
    "sku": fields.String(description="SKU Code"),
    "price": fields.Float(min=0.0, description="Price in VND"),
    "stock_quantity": fields.Integer(min=0, description="Stock quantity"),
    "image_url": fields.String(description="Product photo URL"),
    "description": fields.String(description="Product description"),
    "is_available": fields.Boolean(description="Availability flag")
})

product_stock_patch_model = ns_products.model("ProductStockPatchRequest", {
    "stock_quantity": fields.Integer(required=True, description="Stock value or adjustment amount"),
    "mode": fields.String(default="set", description="Update mode: 'set', 'increment', or 'decrement'")
})

product_availability_patch_model = ns_products.model("ProductAvailabilityPatchRequest", {
    "is_available": fields.Boolean(required=True, description="Target availability state")
})

product_stats_model = ns_products.model("ProductStatsResponse", {
    "total_products": fields.Integer,
    "available_products": fields.Integer,
    "out_of_stock_products": fields.Integer,
    "total_stock_units": fields.Integer,
    "total_inventory_value": fields.Float
})

match_scan_model = ns_products.model("MatchScanRequest", {
    "record_id": fields.String(required=True, description="Target camera scan record ID")
})


@ns_products.route("/count")
class ProductCount(Resource):
    @ns_products.doc("count_products", description="Count available products in store")
    @ns_products.param("category_id", "Filter by category ID", type=str)
    @ns_products.param("is_available", "Filter by availability status", type=bool)
    @ns_products.response(200, "Success", count_model)
    def get(self):
        category_id = request.args.get("category_id", type=str)
        is_available_raw = request.args.get("is_available")

        with get_db_session() as session:
            stmt = select(func.count(Product.id))
            if category_id:
                stmt = stmt.where(Product.category_id == category_id)
            if is_available_raw is not None:
                is_available = is_available_raw.lower() in ("true", "1", "t")
                stmt = stmt.where(Product.is_available == is_available)
            count = session.exec(stmt).one()
            return {"count": count}, 200


@ns_products.route("/stats")
class ProductStats(Resource):
    @ns_products.doc("get_product_stats", description="Aggregate product and inventory statistics")
    @ns_products.response(200, "Success", product_stats_model)
    def get(self):
        with get_db_session() as session:
            all_prods = session.exec(select(Product)).all()
            total = len(all_prods)
            available = sum(1 for p in all_prods if p.is_available)
            out_of_stock = sum(1 for p in all_prods if p.stock_quantity <= 0)
            total_stock = sum(p.stock_quantity for p in all_prods)
            total_val = sum(p.stock_quantity * p.price for p in all_prods)

            return {
                "total_products": total,
                "available_products": available,
                "out_of_stock_products": out_of_stock,
                "total_stock_units": total_stock,
                "total_inventory_value": round(total_val, 2)
            }, 200


@ns_products.route("/match-from-scan")
class ProductMatchFromScan(Resource):
    @ns_products.doc("match_from_scan", description="Match detected objects from camera scan record to shop products")
    @ns_products.expect(match_scan_model, validate=True)
    @ns_products.response(200, "Matching products retrieved", [product_model])
    @ns_products.response(404, "Scan record not found")
    def post(self):
        data = request.json or {}
        record_id = data.get("record_id")
        if not record_id:
            return {"detail": "Thiếu record_id."}, 400

        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Không tìm thấy bản ghi quét ID {record_id}."}, 404

            detected_objects = []
            try:
                detected_objects = json.loads(record.ocr_json_data)
            except Exception:
                pass

            raw_names = [
                obj.get("name", "").strip().lower()
                for obj in detected_objects
                if isinstance(obj, dict) and obj.get("name")
            ]
            unique_classes = list(set(filter(None, raw_names)))

            if not unique_classes:
                return [], 200

            stmt = select(Product).where(
                func.lower(Product.class_name).in_(unique_classes),
                Product.is_available == True
            )
            matched_products = session.exec(stmt).all()

            return [
                {
                    "id": p.id,
                    "category_id": p.category_id,
                    "name": p.name,
                    "class_name": p.class_name,
                    "sku": p.sku,
                    "price": p.price,
                    "stock_quantity": p.stock_quantity,
                    "image_url": p.image_url,
                    "description": p.description,
                    "is_available": p.is_available,
                    "created_at": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at)
                }
                for p in matched_products
            ], 200


@ns_products.route("")
class ProductListCreate(Resource):
    @ns_products.doc("list_products", description="List products with optional search query and category filter")
    @ns_products.param("category_id", "Filter by category ID", type=str)
    @ns_products.param("search", "Search by product title or SKU", type=str)
    @ns_products.param("limit", "Page size", type=int, default=10)
    @ns_products.param("skip", "Offset", type=int, default=0)
    @ns_products.response(200, "Success", [product_model])
    def get(self):
        category_id = request.args.get("category_id", type=str)
        search_query = request.args.get("search") or request.args.get("q")
        limit = request.args.get("limit", default=10, type=int)
        skip = request.args.get("skip", default=0, type=int)

        with get_db_session() as session:
            stmt = select(Product)
            if category_id:
                stmt = stmt.where(Product.category_id == category_id)
            if search_query:
                term = f"%{search_query.strip().lower()}%"
                stmt = stmt.where((func.lower(Product.name).like(term)) | (func.lower(Product.sku).like(term)))
            stmt = stmt.order_by(Product.id.asc()).offset(skip).limit(limit)

            products = session.exec(stmt).all()
            return [
                {
                    "id": p.id,
                    "category_id": p.category_id,
                    "name": p.name,
                    "class_name": p.class_name,
                    "sku": p.sku,
                    "price": p.price,
                    "stock_quantity": p.stock_quantity,
                    "image_url": p.image_url,
                    "description": p.description,
                    "is_available": p.is_available,
                    "created_at": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at)
                }
                for p in products
            ], 200

    @ns_products.doc("create_product", security="Bearer", description="Create new product item")
    @ns_products.expect(product_create_model, validate=True)
    @ns_products.response(201, "Product created", product_model)
    @ns_products.response(400, "Duplicate SKU or validation error")
    @admin_required
    def post(self, current_user: dict):
        data = request.json or {}
        name = data.get("name", "").strip()
        price = float(data.get("price", 0.0))
        sku = data.get("sku", "").strip() or None
        class_name = data.get("class_name", "").strip().lower() or None

        if not name or price < 0:
            return {"detail": "Tên và giá sản phẩm không hợp lệ."}, 400

        with get_db_session() as session:
            if sku:
                existing_sku = session.exec(select(Product).where(Product.sku == sku)).first()
                if existing_sku:
                    return {"detail": f"SKU '{sku}' đã được sử dụng."}, 400

            product = Product(
                name=name,
                category_id=data.get("category_id"),
                class_name=class_name,
                sku=sku,
                price=price,
                stock_quantity=int(data.get("stock_quantity", 0)),
                image_url=data.get("image_url"),
                description=data.get("description"),
                is_available=bool(data.get("is_available", True)),
                created_at=datetime.now(timezone.utc)
            )
            session.add(product)
            session.commit()
            session.refresh(product)

            return {
                "id": product.id,
                "category_id": product.category_id,
                "name": product.name,
                "class_name": product.class_name,
                "sku": product.sku,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "image_url": product.image_url,
                "description": product.description,
                "is_available": product.is_available,
                "created_at": product.created_at.isoformat() if hasattr(product.created_at, "isoformat") else str(product.created_at)
            }, 201


@ns_products.route("/<string:product_id>")
class ProductDetail(Resource):
    @ns_products.doc("get_product", description="Get product details by ID")
    @ns_products.response(200, "Success", product_model)
    @ns_products.response(404, "Product not found")
    def get(self, product_id: str):
        with get_db_session() as session:
            product = session.get(Product, product_id)
            if not product:
                return {"detail": f"Product ID {product_id} not found."}, 404
            return {
                "id": product.id,
                "category_id": product.category_id,
                "name": product.name,
                "class_name": product.class_name,
                "sku": product.sku,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "image_url": product.image_url,
                "description": product.description,
                "is_available": product.is_available,
                "created_at": product.created_at.isoformat() if hasattr(product.created_at, "isoformat") else str(product.created_at)
            }, 200

    @ns_products.doc("update_product", security="Bearer", description="Update product price, inventory, or info")
    @ns_products.expect(product_update_model, validate=True)
    @ns_products.response(200, "Product updated", product_model)
    @ns_products.response(404, "Product not found")
    @admin_required
    def put(self, product_id: str, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            product = session.get(Product, product_id)
            if not product:
                return {"detail": f"Product ID {product_id} not found."}, 404

            if "name" in data and data["name"]:
                product.name = data["name"].strip()
            if "category_id" in data:
                product.category_id = data["category_id"]
            if "class_name" in data:
                product.class_name = data["class_name"].strip().lower() if data["class_name"] else None
            if "sku" in data and data["sku"]:
                product.sku = data["sku"].strip()
            if "price" in data and data["price"] is not None:
                product.price = float(data["price"])
            if "stock_quantity" in data and data["stock_quantity"] is not None:
                product.stock_quantity = int(data["stock_quantity"])
            if "image_url" in data:
                product.image_url = data["image_url"]
            if "description" in data:
                product.description = data["description"]
            if "is_available" in data and data["is_available"] is not None:
                product.is_available = bool(data["is_available"])

            session.commit()
            session.refresh(product)

            return {
                "id": product.id,
                "category_id": product.category_id,
                "name": product.name,
                "class_name": product.class_name,
                "sku": product.sku,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "image_url": product.image_url,
                "description": product.description,
                "is_available": product.is_available,
                "created_at": product.created_at.isoformat() if hasattr(product.created_at, "isoformat") else str(product.created_at)
            }, 200

    @ns_products.doc("patch_product", security="Bearer", description="Partially update product details")
    @ns_products.expect(product_patch_model, validate=False)
    @ns_products.response(200, "Product updated", product_model)
    @ns_products.response(404, "Product not found")
    @admin_required
    def patch(self, product_id: str, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            product = session.get(Product, product_id)
            if not product:
                return {"detail": f"Product ID {product_id} not found."}, 404

            if "name" in data and data["name"] is not None:
                product.name = data["name"].strip()
            if "category_id" in data and data["category_id"] is not None:
                product.category_id = data["category_id"]
            if "class_name" in data and data["class_name"] is not None:
                product.class_name = data["class_name"].strip().lower() if data["class_name"] else None
            if "sku" in data and data["sku"] is not None:
                product.sku = data["sku"].strip()
            if "price" in data and data["price"] is not None:
                product.price = float(data["price"])
            if "stock_quantity" in data and data["stock_quantity"] is not None:
                product.stock_quantity = int(data["stock_quantity"])
            if "image_url" in data and data["image_url"] is not None:
                product.image_url = data["image_url"]
            if "description" in data and data["description"] is not None:
                product.description = data["description"]
            if "is_available" in data and data["is_available"] is not None:
                product.is_available = bool(data["is_available"])

            session.commit()
            session.refresh(product)

            return {
                "id": product.id,
                "category_id": product.category_id,
                "name": product.name,
                "class_name": product.class_name,
                "sku": product.sku,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "image_url": product.image_url,
                "description": product.description,
                "is_available": product.is_available,
                "created_at": product.created_at.isoformat() if hasattr(product.created_at, "isoformat") else str(product.created_at)
            }, 200

    @ns_products.doc("delete_product", security="Bearer", description="Delete product from store")
    @ns_products.response(200, "Product deleted", message_model)
    @ns_products.response(404, "Product not found")
    @admin_required
    def delete(self, product_id: str, current_user: dict):
        with get_db_session() as session:
            product = session.get(Product, product_id)
            if not product:
                return {"detail": f"Product ID {product_id} not found."}, 404
            session.delete(product)
            session.commit()
            return {"message": f"Product ID {product_id} deleted successfully.", "success": True}, 200


@ns_products.route("/<string:product_id>/stock")
class ProductStockResource(Resource):
    @ns_products.doc("patch_product_stock", security="Bearer", description="Adjust product stock quantity (set, increment, decrement)")
    @ns_products.expect(product_stock_patch_model, validate=True)
    @ns_products.response(200, "Stock updated", product_model)
    @ns_products.response(404, "Product not found")
    @admin_required
    def patch(self, product_id: str, current_user: dict):
        data = request.json or {}
        qty = int(data.get("stock_quantity", 0))
        mode = data.get("mode", "set").lower()

        with get_db_session() as session:
            product = session.get(Product, product_id)
            if not product:
                return {"detail": f"Product ID {product_id} not found."}, 404

            if mode == "increment":
                product.stock_quantity += qty
            elif mode == "decrement":
                product.stock_quantity = max(0, product.stock_quantity - qty)
            else:
                product.stock_quantity = max(0, qty)

            session.commit()
            session.refresh(product)
            return {
                "id": product.id,
                "category_id": product.category_id,
                "name": product.name,
                "class_name": product.class_name,
                "sku": product.sku,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "image_url": product.image_url,
                "description": product.description,
                "is_available": product.is_available,
                "created_at": product.created_at.isoformat() if hasattr(product.created_at, "isoformat") else str(product.created_at)
            }, 200


@ns_products.route("/<string:product_id>/availability")
class ProductAvailabilityResource(Resource):
    @ns_products.doc("patch_product_availability", security="Bearer", description="Toggle or set product availability")
    @ns_products.expect(product_availability_patch_model, validate=True)
    @ns_products.response(200, "Availability updated", product_model)
    @ns_products.response(404, "Product not found")
    @admin_required
    def patch(self, product_id: str, current_user: dict):
        data = request.json or {}
        is_avail = bool(data.get("is_available", True))

        with get_db_session() as session:
            product = session.get(Product, product_id)
            if not product:
                return {"detail": f"Product ID {product_id} not found."}, 404

            product.is_available = is_avail
            session.commit()
            session.refresh(product)
            return {
                "id": product.id,
                "category_id": product.category_id,
                "name": product.name,
                "class_name": product.class_name,
                "sku": product.sku,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "image_url": product.image_url,
                "description": product.description,
                "is_available": product.is_available,
                "created_at": product.created_at.isoformat() if hasattr(product.created_at, "isoformat") else str(product.created_at)
            }, 200

