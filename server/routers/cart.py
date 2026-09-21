from datetime import datetime, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from sqlmodel import select

from server.core.common_models import message_model
from server.core.security import token_required
from server.database import get_db_session
from server.models.cart import CartItem
from server.models.product import Product

ns_cart = Namespace("E-Commerce Cart Management", path="/api/v1/cart", description="Shopping cart lifecycle and operations")
ns_cart.add_model("MessageResponse", message_model)

cart_item_detail_model = ns_cart.model("CartItemDetail", {
    "id": fields.String,
    "product_id": fields.String,
    "product_name": fields.String,
    "product_price": fields.Float,
    "product_image": fields.String,
    "class_name": fields.String,
    "record_id": fields.String,
    "quantity": fields.Integer,
    "item_total": fields.Float
})

cart_response_model = ns_cart.model("CartResponse", {
    "items": fields.List(fields.Nested(cart_item_detail_model)),
    "total_items": fields.Integer,
    "total_amount": fields.Float
})

cart_add_model = ns_cart.model("CartAddRequest", {
    "product_id": fields.String(required=True, description="Product ID to add"),
    "quantity": fields.Integer(default=1, min=1, description="Quantity to add"),
    "record_id": fields.String(required=False, description="Scan record ID where item was detected")
})

cart_update_model = ns_cart.model("CartItemUpdateRequest", {
    "quantity": fields.Integer(required=True, min=0, description="New quantity (0 deletes item)")
})

cart_patch_model = ns_cart.model("CartItemPatchRequest", {
    "quantity": fields.Integer(required=False, description="Exact quantity to set (0 deletes item)"),
    "delta": fields.Integer(required=False, description="Incremental change (e.g. +1 or -1)")
})

cart_summary_model = ns_cart.model("CartSummaryResponse", {
    "total_items": fields.Integer,
    "unique_products": fields.Integer,
    "total_amount": fields.Float
})


@ns_cart.route("")
class CartResource(Resource):
    @ns_cart.doc("get_cart", security="Bearer", description="Get user shopping cart items and subtotal")
    @ns_cart.response(200, "Success", cart_response_model)
    @token_required
    def get(self, current_user: dict):
        with get_db_session() as session:
            stmt = select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.user_id == current_user["id"])
            results = session.exec(stmt).all()

            items = []
            total_amount = 0.0
            total_items = 0

            for cart_item, product in results:
                item_total = cart_item.quantity * product.price
                total_amount += item_total
                total_items += cart_item.quantity
                items.append({
                    "id": cart_item.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_price": product.price,
                    "product_image": product.image_url or "",
                    "class_name": product.class_name or "",
                    "record_id": cart_item.record_id,
                    "quantity": cart_item.quantity,
                    "item_total": round(item_total, 2)
                })

            return {
                "items": items,
                "total_items": total_items,
                "total_amount": round(total_amount, 2)
            }, 200

    @ns_cart.doc("clear_cart", security="Bearer", description="Clear all items from user cart")
    @ns_cart.response(200, "Cart cleared", message_model)
    @token_required
    def delete(self, current_user: dict):
        with get_db_session() as session:
            items = session.exec(select(CartItem).where(CartItem.user_id == current_user["id"])).all()
            for it in items:
                session.delete(it)
            session.commit()
            return {"message": "Đã xóa sạch giỏ hàng.", "success": True}, 200


@ns_cart.route("/summary")
class CartSummaryResource(Resource):
    @ns_cart.doc("get_cart_summary", security="Bearer", description="Get high-level summary of items and totals in user cart")
    @ns_cart.response(200, "Success", cart_summary_model)
    @token_required
    def get(self, current_user: dict):
        with get_db_session() as session:
            stmt = select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.user_id == current_user["id"])
            results = session.exec(stmt).all()
            total_items = sum(it.quantity for it, _ in results)
            total_amount = sum(it.quantity * prod.price for it, prod in results)
            return {
                "total_items": total_items,
                "unique_products": len(results),
                "total_amount": round(total_amount, 2)
            }, 200


@ns_cart.route("/items")
class CartAddResource(Resource):
    @ns_cart.doc("add_to_cart", security="Bearer", description="Add product item to cart (with optional camera scan link)")
    @ns_cart.expect(cart_add_model, validate=True)
    @ns_cart.response(201, "Added to cart", cart_item_detail_model)
    @ns_cart.response(400, "Product not available")
    @token_required
    def post(self, current_user: dict):
        data = request.json or {}
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))
        record_id = data.get("record_id")

        if quantity <= 0:
            return {"detail": "Số lượng thêm vào giỏ phải lớn hơn 0."}, 400

        with get_db_session() as session:
            product = session.get(Product, product_id)
            if not product or not product.is_available:
                return {"detail": f"Sản phẩm ID {product_id} không tồn tại hoặc đã ngừng kinh doanh."}, 400

            existing = session.exec(
                select(CartItem).where(CartItem.user_id == current_user["id"], CartItem.product_id == product_id)
            ).first()

            if existing:
                existing.quantity += quantity
                if record_id:
                    existing.record_id = record_id
                target_item = existing
            else:
                target_item = CartItem(
                    user_id=current_user["id"],
                    product_id=product_id,
                    record_id=record_id,
                    quantity=quantity,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(target_item)

            session.commit()
            session.refresh(target_item)

            item_total = target_item.quantity * product.price
            return {
                "id": target_item.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_price": product.price,
                "product_image": product.image_url or "",
                "class_name": product.class_name or "",
                "record_id": target_item.record_id,
                "quantity": target_item.quantity,
                "item_total": round(item_total, 2)
            }, 201


@ns_cart.route("/items/<string:item_id>")
class CartItemResource(Resource):
    @ns_cart.doc("update_cart_item", security="Bearer", description="Update quantity of cart item (quantity=0 deletes it)")
    @ns_cart.expect(cart_update_model, validate=True)
    @ns_cart.response(200, "Updated", cart_item_detail_model)
    @ns_cart.response(404, "Cart item not found")
    @token_required
    def put(self, item_id: str, current_user: dict):
        data = request.json or {}
        new_quantity = int(data.get("quantity", 1))

        with get_db_session() as session:
            item = session.get(CartItem, item_id)
            if not item or item.user_id != current_user["id"]:
                return {"detail": f"Không tìm thấy món hàng ID {item_id} trong giỏ."}, 404

            product = session.get(Product, item.product_id)
            if not product:
                session.delete(item)
                session.commit()
                return {"detail": "Sản phẩm không còn tồn tại."}, 404

            if new_quantity <= 0:
                session.delete(item)
                session.commit()
                return {"message": "Đã xóa sản phẩm khỏi giỏ hàng.", "success": True}, 200

            item.quantity = new_quantity
            session.commit()
            session.refresh(item)

            item_total = item.quantity * product.price
            return {
                "id": item.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_price": product.price,
                "product_image": product.image_url or "",
                "class_name": product.class_name or "",
                "record_id": item.record_id,
                "quantity": item.quantity,
                "item_total": round(item_total, 2)
            }, 200

    @ns_cart.doc("patch_cart_item", security="Bearer", description="Partially update cart item quantity (set or delta)")
    @ns_cart.expect(cart_patch_model, validate=False)
    @ns_cart.response(200, "Updated", cart_item_detail_model)
    @ns_cart.response(404, "Cart item not found")
    @token_required
    def patch(self, item_id: str, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            item = session.get(CartItem, item_id)
            if not item or item.user_id != current_user["id"]:
                return {"detail": f"Không tìm thấy món hàng ID {item_id} trong giỏ."}, 404

            product = session.get(Product, item.product_id)
            if not product:
                session.delete(item)
                session.commit()
                return {"detail": "Sản phẩm không còn tồn tại."}, 404

            if "delta" in data and data["delta"] is not None:
                item.quantity += int(data["delta"])
            elif "quantity" in data and data["quantity"] is not None:
                item.quantity = int(data["quantity"])

            if item.quantity <= 0:
                session.delete(item)
                session.commit()
                return {"message": "Đã xóa sản phẩm khỏi giỏ hàng.", "success": True}, 200

            session.commit()
            session.refresh(item)

            item_total = item.quantity * product.price
            return {
                "id": item.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_price": product.price,
                "product_image": product.image_url or "",
                "class_name": product.class_name or "",
                "record_id": item.record_id,
                "quantity": item.quantity,
                "item_total": round(item_total, 2)
            }, 200

    @ns_cart.doc("remove_cart_item", security="Bearer", description="Remove single item from cart")
    @ns_cart.response(200, "Item removed", message_model)
    @ns_cart.response(404, "Cart item not found")
    @token_required
    def delete(self, item_id: str, current_user: dict):
        with get_db_session() as session:
            item = session.get(CartItem, item_id)
            if not item or item.user_id != current_user["id"]:
                return {"detail": f"Không tìm thấy món hàng ID {item_id} trong giỏ."}, 404
            session.delete(item)
            session.commit()
            return {"message": f"Đã xóa món hàng ID {item_id} khỏi giỏ.", "success": True}, 200

