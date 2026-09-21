from typing import Any, Dict, List
import reflex as rx
from api.client import api_client, resolve_media_url


class ProductState(rx.State):
    """Hook quản lý danh mục sản phẩm, bộ lọc, tìm kiếm và Visual Search khớp từ ảnh quét."""

    products: List[Dict[str, Any]] = []
    matched_products: List[Dict[str, Any]] = []
    categories: List[Dict[str, Any]] = []

    selected_category: str = ""
    search_query: str = ""
    is_loading_products: bool = False
    is_matched_modal_open: bool = False
    error_message: str = ""

    stats: Dict[str, Any] = {
        "total_products": 0,
        "available_products": 0,
        "out_of_stock_products": 0,
        "total_stock_units": 0,
        "total_inventory_value": 0.0,
    }

    async def fetch_stats(self) -> None:
        """Lấy thống kê kho hàng tổng quan từ GET /products/stats."""
        data, err = await api_client.get("/products/stats")
        if err or not isinstance(data, dict):
            return
        self.stats = data

    async def update_stock(self, product_id: str, quantity: int, mode: str = "increment") -> None:
        """Điều chỉnh tồn kho sản phẩm qua PATCH /products/{id}/stock."""
        from state.auth_state import AuthState
        auth = await self.get_state(AuthState)
        if not auth.token:
            return

        payload = {"stock_quantity": abs(quantity), "mode": "decrement" if quantity < 0 and mode == "increment" else mode}
        data, err = await api_client.patch(f"/products/{product_id}/stock", json_data=payload, token=auth.token)
        if err:
            return rx.toast(f"Lỗi cập nhật kho: {err}", position="top-center")

        await self.fetch_products()
        await self.fetch_stats()
        return rx.toast("Đã cập nhật tồn kho thành công!", position="top-center")

    async def reload_catalog(self) -> None:
        """Nạp lại danh sách sản phẩm và thống kê kho."""
        await self.fetch_stats()
        await self.fetch_products()

    async def fetch_categories(self) -> None:
        """Lấy danh sách các danh mục hàng hóa từ GET /categories."""
        data, err = await api_client.get("/categories")
        if err or not data:
            return

        self.categories = data if isinstance(data, list) else data.get("categories", [])

    async def fetch_products(self, page: Any = 1, limit: Any = 20) -> None:
        """Tải danh sách sản phẩm có áp dụng bộ lọc danh mục, tìm kiếm và phân trang."""
        p = int(page) if isinstance(page, (int, str)) and str(page).isdigit() else 1
        lim = int(limit) if isinstance(limit, (int, str)) and str(limit).isdigit() else 20
        self.is_loading_products = True
        params: Dict[str, Any] = {
            "limit": lim,
            "offset": (p - 1) * lim,
        }

        if self.selected_category:
            params["category_id"] = self.selected_category
        if self.search_query.strip():
            params["search"] = self.search_query.strip()

        data, err = await api_client.get("/products", params=params)
        self.is_loading_products = False

        if err or data is None:
            self.error_message = err or "Không thể tải danh sách sản phẩm."
            return

        raw_list = data if isinstance(data, list) else data.get("items", [])
        for item in raw_list:
            item["image_url"] = resolve_media_url(item.get("image_url"))
            p_price = float(item.get("price") or 0.0)
            item["formatted_price"] = f"{p_price:,.0f} đ".replace(",", ".")
            item["is_in_stock"] = bool(item.get("is_available", True)) and int(item.get("stock_quantity") or 0) > 0
        self.products = raw_list
        self.error_message = ""

    def set_search_query(self, query: str) -> None:
        self.search_query = query

    async def apply_search(self) -> None:
        await self.fetch_products()

    def handle_search_key(self, key: str):
        if key == "Enter":
            return self.apply_search()

    async def select_category(self, category_id: str) -> None:
        self.selected_category = category_id
        await self.fetch_products()

    async def match_from_scan(self, record_id: str) -> None:
        """Visual Search: Gọi POST /products/match-from-scan để tìm sản phẩm tương ứng với ảnh vừa quét."""
        if not record_id:
            return

        self.is_loading_products = True
        payload = {"record_id": record_id}

        data, err = await api_client.post("/products/match-from-scan", json_data=payload)
        self.is_loading_products = False

        if err or not isinstance(data, list):
            self.matched_products = []
            return

        for prod in data:
            prod["image_url"] = resolve_media_url(prod.get("image_url"))
            p_price = float(prod.get("price") or 0.0)
            prod["formatted_price"] = f"{p_price:,.0f} đ".replace(",", ".")
            prod["is_in_stock"] = bool(prod.get("is_available", True)) and int(prod.get("stock_quantity") or 0) > 0

        self.matched_products = data
        if self.matched_products:
            # Tự động mở Modal/Drawer kết quả tìm kiếm khi có sản phẩm phù hợp
            self.is_matched_modal_open = True

    def close_matched_modal(self) -> None:
        self.is_matched_modal_open = False

    def clear_matched_products(self) -> None:
        self.matched_products = []
        self.is_matched_modal_open = False

    async def on_mount(self) -> None:
        """Sự kiện nạp dữ liệu ban đầu khi component gắn kết vào DOM."""
        await self.fetch_categories()
        await self.fetch_products()
