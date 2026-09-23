import re
import sqlite3
from datetime import datetime, timezone
from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import create_engine, text
from sqlmodel import select

from server.core.security import admin_required
from server.database import DB_PATH, get_db_session
from server.models.ocr_record import OCRRecord
from server.models.order import Order
from server.models.product import Product

ns_copilot = Namespace("Admin Copilot & Safe SQL", path="/api/v1/copilot", description="Natural Language to Safe Read-Only SQL Copilot & Executive Briefing")

# Hardened Read-Only SQLite Engine via OS URI mode=ro
_ro_uri = f"file:///{DB_PATH.as_posix()}?mode=ro"
ro_engine = create_engine(
    "sqlite://",
    creator=lambda: sqlite3.connect(_ro_uri, uri=True, check_same_thread=False),
    echo=False
)

copilot_query_request_model = ns_copilot.model("CopilotQueryRequest", {
    "query": fields.String(required=True, description="Natural language search or question in Vietnamese")
})

copilot_query_response_model = ns_copilot.model("CopilotQueryResponse", {
    "query": fields.String,
    "intent": fields.String,
    "safe_sql": fields.String,
    "count": fields.Integer,
    "results": fields.List(fields.Raw),
    "route_suggestion": fields.String,
    "explanation": fields.String
})

daily_briefing_response_model = ns_copilot.model("ExecutiveDailyBriefingResponse", {
    "summary": fields.String,
    "metrics": fields.Raw,
    "generated_at": fields.String
})

# Forbidden keywords for Defense-in-depth Layer 1
BANNED_SQL_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|PRAGMA|ATTACH|DETACH|EXECUTE|GRANT|REVOKE|VACUUM)\b|"
    r";|/\*|\*/|--",
    re.IGNORECASE
)


def _parse_natural_language_to_safe_query(nl_query: str) -> tuple[str, str, str, str]:
    """
    Translates Vietnamese natural language administrative inquiries into
    strictly safe SELECT statements and UI routing suggestions.
    """
    q = nl_query.strip().lower()

    # Pattern 1: Bản ghi quét camera lỗi hoặc cần duyệt
    if any(k in q for k in ["lỗi", "chưa duyệt", "chờ duyệt", "pending", "rejected", "kiểm duyệt"]):
        sql = "SELECT id, user_id, raw_detected_text, status, created_at FROM ocr_records WHERE status IN ('pending', 'rejected') ORDER BY created_at DESC"
        intent = "filter_records_pending_rejected"
        route = "/admin/reviews"
        explanation = "Tra cứu các bản ghi quét ảnh đang ở trạng thái 'pending' hoặc 'rejected' cần kiểm duyệt."
        return sql, intent, route, explanation

    # Pattern 2: Sản phẩm laptop hoặc tồn kho thấp
    if any(k in q for k in ["laptop", "máy tính", "bán chạy", "tồn kho", "stock", "dưới"]):
        sql = "SELECT id, name, sku, class_name, price, stock_quantity, is_available FROM products WHERE stock_quantity <= 10 OR LOWER(class_name) LIKE '%laptop%' ORDER BY stock_quantity ASC"
        intent = "filter_products_inventory_low"
        route = "/admin/products"
        explanation = "Lọc các sản phẩm có lượng tồn kho dưới ngưỡng an toàn (<= 10) hoặc liên quan đến danh mục laptop."
        return sql, intent, route, explanation

    # Pattern 3: Đơn hàng hoặc doanh thu
    if any(k in q for k in ["đơn hàng", "doanh thu", "orders", "thanh toán", "revenue"]):
        sql = "SELECT id, user_id, total_amount, shipping_address, phone_number, status, created_at FROM orders ORDER BY created_at DESC"
        intent = "query_orders"
        route = "/admin"
        explanation = "Tổng hợp danh sách các đơn đặt hàng mới nhất trong hệ thống."
        return sql, intent, route, explanation

    # Pattern 4: Bản ghi quét hôm nay
    if any(k in q for k in ["hôm nay", "today"]):
        sql = "SELECT id, user_id, raw_detected_text, status, created_at FROM ocr_records WHERE date(created_at) = date('now') ORDER BY created_at DESC"
        intent = "query_records_today"
        route = "/admin/records"
        explanation = "Hiển thị tất cả các lượt quét ảnh camera được thực hiện trong ngày hôm nay."
        return sql, intent, route, explanation

    # Fallback: Tra cứu sản phẩm theo từ khóa an toàn
    cleaned_terms = re.sub(r"[^a-zA-Z0-9\s\u00C0-\u1EF9]", "", q).strip()
    term = f"%{cleaned_terms}%"
    sql = f"SELECT id, name, sku, class_name, price, stock_quantity FROM products WHERE LOWER(name) LIKE '{term.lower()}' OR LOWER(class_name) LIKE '{term.lower()}' ORDER BY id ASC"
    intent = "search_products_general"
    route = f"/admin/products?search={cleaned_terms}"
    explanation = f"Tìm kiếm sản phẩm hoặc mã nhãn trùng khớp với từ khóa '{cleaned_terms}'."
    return sql, intent, route, explanation


@ns_copilot.route("/query")
class CopilotQueryResource(Resource):
    @ns_copilot.doc("copilot_query", security="Bearer", description="Safe Natural Language or Read-Only SELECT query execution")
    @ns_copilot.expect(copilot_query_request_model, validate=True)
    @ns_copilot.response(200, "Success", copilot_query_response_model)
    @ns_copilot.response(400, "Invalid or prohibited query")
    @admin_required
    def post(self, current_user: dict):
        data = request.json or {}
        raw_query = (data.get("query") or "").strip()
        if not raw_query:
            return {"detail": "Nội dung truy vấn không được để trống."}, 400

        # Layer 1: Check if the user passed raw SQL directly or natural language
        if raw_query.upper().startswith("SELECT"):
            sql_candidate = raw_query
            intent = "raw_safe_sql"
            route = None
            explanation = "Thực thi truy vấn SELECT an toàn trực tiếp."
        else:
            sql_candidate, intent, route, explanation = _parse_natural_language_to_safe_query(raw_query)

        # Layer 1 Whitelist & Sanitization Check
        trimmed = sql_candidate.strip()
        if not re.match(r"^SELECT\s+", trimmed, re.IGNORECASE):
            return {"detail": "Khóa an toàn: Chỉ cho phép các câu lệnh SELECT (Read-only)."}, 400

        if BANNED_SQL_PATTERNS.search(trimmed):
            return {"detail": "Khóa an toàn: Phát hiện từ khóa hoặc ký tự bị cấm (DDL/DML/Chaining injection)."}, 400

        # Layer 3: Hard Subquery Wrapping with LIMIT 50
        bounded_sql = f"SELECT * FROM ({trimmed}) AS safe_subquery LIMIT 50"

        # Layer 2: Execute strictly against OS-level Read-Only SQLite engine
        results = []
        try:
            with ro_engine.connect() as conn:
                cursor = conn.execute(text(bounded_sql))
                columns = list(cursor.keys())
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
        except Exception as ex:
            return {
                "detail": f"Lỗi thực thi truy vấn an toàn: {str(ex)}",
                "safe_sql": bounded_sql
            }, 400

        return {
            "query": raw_query,
            "intent": intent,
            "safe_sql": bounded_sql,
            "count": len(results),
            "results": results,
            "route_suggestion": route,
            "explanation": explanation
        }, 200


@ns_copilot.route("/daily-briefing")
class CopilotDailyBriefingResource(Resource):
    @ns_copilot.doc("daily_briefing", description="Executive daily summary synthesizing scans, stockout risks, and reviews")
    @ns_copilot.response(200, "Success", daily_briefing_response_model)
    def get(self):
        with get_db_session() as session:
            # 1. Scans today
            scans_row = session.exec(text("SELECT COUNT(*) FROM ocr_records WHERE date(created_at) = date('now')")).one()
            scans_today = int(scans_row[0])

            # 2. Low stock items
            low_stock_prods = session.exec(
                select(Product).where(Product.stock_quantity <= 10).order_by(Product.stock_quantity.asc())
            ).all()
            low_stock_count = len(low_stock_prods)
            at_risk_classes = list(set(
                f"#{p.class_name.lstrip('#')}" for p in low_stock_prods if p.class_name
            ))[:4]

            # 3. Pending reviews
            pending_row = session.exec(text("SELECT COUNT(*) FROM ocr_records WHERE status = 'pending'")).one()
            pending_reviews = int(pending_row[0])

            # 4. Revenue today
            revenue_row = session.exec(text("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE date(created_at) = date('now')")).one()
            revenue_today = float(revenue_row[0])

            risk_desc = f" ({', '.join(at_risk_classes)})" if at_risk_classes else ""
            summary = (
                f"Hôm nay có {scans_today} lượt quét camera, {low_stock_count} sản phẩm có nguy cơ hết hàng{risk_desc}, "
                f"{pending_reviews} bản ghi AI cần kiểm duyệt lại."
            )

            return {
                "summary": summary,
                "metrics": {
                    "scans_today": scans_today,
                    "low_stock_count": low_stock_count,
                    "pending_reviews_count": pending_reviews,
                    "revenue_today": revenue_today,
                    "at_risk_classes": at_risk_classes
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }, 200
