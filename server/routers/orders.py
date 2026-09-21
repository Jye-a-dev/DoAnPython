from datetime import datetime, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from sqlmodel import select

from server.core.config import executor, logger
from server.core.pipeline_client import call_pipeline_tts
from server.core.security import admin_required, token_required
from server.database import get_db_session
from server.models.cart import CartItem
from server.models.order import Order, OrderItem
from server.models.product import Product

ns_orders = Namespace("E-Commerce Orders & Checkout", path="/api/v1/orders", description="Order checkout with automated audio confirmation")

order_item_read_model = ns_orders.model("OrderItemRead", {
    "id": fields.Integer,
    "order_id": fields.Integer,
    "product_id": fields.Integer,
    "product_name": fields.String,
    "quantity": fields.Integer,
    "unit_price": fields.Float
})

order_read_model = ns_orders.model("OrderRead", {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "total_amount": fields.Float,
    "shipping_address": fields.String,
    "phone_number": fields.String,
    "status": fields.String,
    "audio_confirmation_url": fields.String,
    "created_at": fields.String,
    "items": fields.List(fields.Nested(order_item_read_model))
})

checkout_request_model = ns_orders.model("CheckoutRequest", {
    "shipping_address": fields.String(required=True, description="Delivery shipping address"),
    "phone_number": fields.String(required=True, description="Contact phone number")
})

order_status_update_model = ns_orders.model("OrderStatusUpdateRequest", {
    "status": fields.String(required=True, description="New status: pending, paid, shipped, cancelled")
})


@ns_orders.route("/checkout")
class OrderCheckout(Resource):
    @ns_orders.doc("checkout", security="Bearer", description="Convert cart into placed order, deduct inventory, and synthesize audio confirmation non-blockingly")
    @ns_orders.expect(checkout_request_model, validate=True)
    @ns_orders.response(201, "Order confirmed", order_read_model)
    @ns_orders.response(400, "Cart empty or insufficient stock")
    @token_required
    def post(self, current_user: dict):
        data = request.json or {}
        shipping_address = data.get("shipping_address", "").strip()
        phone_number = data.get("phone_number", "").strip()

        if not shipping_address or not phone_number:
            return {"detail": "Địa chỉ giao hàng và số điện thoại là bắt buộc."}, 400

        with get_db_session() as session:
            cart_query = select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.user_id == current_user["id"])
            cart_rows = session.exec(cart_query).all()

            if not cart_rows:
                return {"detail": "Giỏ hàng của bạn đang trống."}, 400

            for cart_item, product in cart_rows:
                if product.stock_quantity < cart_item.quantity:
                    return {
                        "detail": f"Sản phẩm '{product.name}' chỉ còn {product.stock_quantity} trong kho, không đủ số lượng yêu cầu ({cart_item.quantity})."
                    }, 400

            total_amount = sum(cart_item.quantity * product.price for cart_item, product in cart_rows)

            order = Order(
                user_id=current_user["id"],
                total_amount=round(total_amount, 2),
                shipping_address=shipping_address,
                phone_number=phone_number,
                status="pending",
                audio_confirmation_url="",
                created_at=datetime.now(timezone.utc)
            )
            session.add(order)
            session.commit()
            session.refresh(order)

            order_items_read = []
            for cart_item, product in cart_rows:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=cart_item.quantity,
                    unit_price=product.price
                )
                session.add(order_item)
                product.stock_quantity -= cart_item.quantity
                session.delete(cart_item)

                order_items_read.append({
                    "id": order_item.id or 0,
                    "order_id": order.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": cart_item.quantity,
                    "unit_price": product.price
                })

            session.commit()
            order_id = order.id
            order_user_id = order.user_id
            total_val = order.total_amount
            order_address = order.shipping_address
            order_phone = order.phone_number
            order_status = order.status
            order_created_at = order.created_at.isoformat() if hasattr(order.created_at, "isoformat") else str(order.created_at)

        # Asynchronous non-blocking TTS audio synthesis in background (fire-and-forget)
        def background_order_audio(o_id: int, val: float) -> None:
            try:
                msg = f"Đơn hàng mã số {o_id} trị giá {int(val):,} đồng đã được xác nhận thành công. Cảm ơn bạn!"
                audio_url = call_pipeline_tts(msg)
                if audio_url:
                    with get_db_session() as s2:
                        o_db = s2.get(Order, o_id)
                        if o_db:
                            o_db.audio_confirmation_url = audio_url
                            s2.commit()
            except Exception as ex:
                logger.warning(f"Async audio confirmation failed for order {o_id}: {str(ex)}")

        executor.submit(background_order_audio, order_id, total_val)

        return {
            "id": order_id,
            "user_id": order_user_id,
            "total_amount": total_val,
            "shipping_address": order_address,
            "phone_number": order_phone,
            "status": order_status,
            "audio_confirmation_url": None,
            "created_at": order_created_at,
            "items": order_items_read
        }, 201


@ns_orders.route("")
class OrderListResource(Resource):
    @ns_orders.doc("list_orders", security="Bearer", description="List placed orders for current user (or all if admin)")
    @ns_orders.response(200, "Success", [order_read_model])
    @token_required
    def get(self, current_user: dict):
        with get_db_session() as session:
            stmt = select(Order)
            if current_user["role_id"] != 1:
                stmt = stmt.where(Order.user_id == current_user["id"])
            stmt = stmt.order_by(Order.id.desc())

            orders = session.exec(stmt).all()
            output = []
            for o in orders:
                items_query = select(OrderItem, Product).join(Product, OrderItem.product_id == Product.id).where(OrderItem.order_id == o.id)
                item_rows = session.exec(items_query).all()
                items_list = [
                    {
                        "id": oi.id,
                        "order_id": oi.order_id,
                        "product_id": oi.product_id,
                        "product_name": prod.name,
                        "quantity": oi.quantity,
                        "unit_price": oi.unit_price
                    }
                    for oi, prod in item_rows
                ]
                output.append({
                    "id": o.id,
                    "user_id": o.user_id,
                    "total_amount": o.total_amount,
                    "shipping_address": o.shipping_address,
                    "phone_number": o.phone_number,
                    "status": o.status,
                    "audio_confirmation_url": o.audio_confirmation_url or "",
                    "created_at": o.created_at.isoformat() if hasattr(o.created_at, "isoformat") else str(o.created_at),
                    "items": items_list
                })
            return output, 200


@ns_orders.route("/<int:order_id>")
class OrderDetailResource(Resource):
    @ns_orders.doc("get_order", security="Bearer", description="Get order details by ID")
    @ns_orders.response(200, "Success", order_read_model)
    @ns_orders.response(403, "Forbidden")
    @ns_orders.response(404, "Order not found")
    @token_required
    def get(self, order_id: int, current_user: dict):
        with get_db_session() as session:
            order = session.get(Order, order_id)
            if not order:
                return {"detail": f"Order ID {order_id} not found."}, 404
            if current_user["role_id"] != 1 and order.user_id != current_user["id"]:
                return {"detail": "Bạn không có quyền xem đơn hàng này."}, 403

            items_query = select(OrderItem, Product).join(Product, OrderItem.product_id == Product.id).where(OrderItem.order_id == order.id)
            item_rows = session.exec(items_query).all()
            items_list = [
                {
                    "id": oi.id,
                    "order_id": oi.order_id,
                    "product_id": oi.product_id,
                    "product_name": prod.name,
                    "quantity": oi.quantity,
                    "unit_price": oi.unit_price
                }
                for oi, prod in item_rows
            ]

            return {
                "id": order.id,
                "user_id": order.user_id,
                "total_amount": order.total_amount,
                "shipping_address": order.shipping_address,
                "phone_number": order.phone_number,
                "status": order.status,
                "audio_confirmation_url": order.audio_confirmation_url or "",
                "created_at": order.created_at.isoformat() if hasattr(order.created_at, "isoformat") else str(order.created_at),
                "items": items_list
            }, 200


@ns_orders.route("/<int:order_id>/status")
class OrderStatusResource(Resource):
    @ns_orders.doc("update_order_status", security="Bearer", description="Update order lifecycle status")
    @ns_orders.expect(order_status_update_model, validate=True)
    @ns_orders.response(200, "Status updated", order_read_model)
    @ns_orders.response(400, "Invalid status")
    @ns_orders.response(404, "Order not found")
    @admin_required
    def put(self, order_id: int, current_user: dict):
        data = request.json or {}
        new_status = data.get("status", "").strip().lower()
        allowed_statuses = {"pending", "paid", "shipped", "cancelled"}

        if new_status not in allowed_statuses:
            return {"detail": f"Trạng thái không hợp lệ. Cho phép: {', '.join(allowed_statuses)}"}, 400

        with get_db_session() as session:
            order = session.get(Order, order_id)
            if not order:
                return {"detail": f"Order ID {order_id} not found."}, 404

            order.status = new_status
            session.commit()
            session.refresh(order)

            items_query = select(OrderItem, Product).join(Product, OrderItem.product_id == Product.id).where(OrderItem.order_id == order.id)
            item_rows = session.exec(items_query).all()
            items_list = [
                {
                    "id": oi.id,
                    "order_id": oi.order_id,
                    "product_id": oi.product_id,
                    "product_name": prod.name,
                    "quantity": oi.quantity,
                    "unit_price": oi.unit_price
                }
                for oi, prod in item_rows
            ]

            return {
                "id": order.id,
                "user_id": order.user_id,
                "total_amount": order.total_amount,
                "shipping_address": order.shipping_address,
                "phone_number": order.phone_number,
                "status": order.status,
                "audio_confirmation_url": order.audio_confirmation_url or "",
                "created_at": order.created_at.isoformat() if hasattr(order.created_at, "isoformat") else str(order.created_at),
                "items": items_list
            }, 200

