from typing import Any, Dict, List, Optional
import reflex as rx
from api.client import api_client, resolve_media_url


class CartState(rx.State):
    """Hook quản lý Giỏ hàng, cập nhật số lượng và Thanh toán với âm thanh xác nhận."""

    cart_items: List[Dict[str, Any]] = []
    total_price: float = 0.0
    checkout_audio_url: str = ""
    is_checking_out: bool = False
    is_cart_open: bool = False
    error_message: str = ""

    shipping_address: str = "123 Nguyen Trai, Q.1, TP.HCM"
    phone_number: str = "0901234567"
    checkout_success: bool = False
    last_order_id: str = ""

    @rx.var
    def total_items(self) -> int:
        """Tổng số lượng sản phẩm trong giỏ hàng."""
        return sum(int(item.get("quantity", 1)) for item in self.cart_items)

    @rx.var
    def total_amount(self) -> float:
        """Alias cho total_price để tương thích giao diện."""
        return self.total_price

    @rx.var
    def formatted_total_amount(self) -> str:
        """Tổng tiền thanh toán định dạng VND."""
        return f"{self.total_price:,.0f} đ".replace(",", ".")

    @rx.var
    def order_audio_url(self) -> str:
        """Alias cho checkout_audio_url."""
        return self.checkout_audio_url

    def open_cart(self) -> None:
        self.is_cart_open = True
        self.checkout_success = False
        self.error_message = ""

    def close_cart(self) -> None:
        self.is_cart_open = False

    def set_address(self, addr: str) -> None:
        self.shipping_address = addr

    def set_phone(self, phone: str) -> None:
        self.phone_number = phone

    async def fetch_cart(self) -> None:
        """Đồng bộ giỏ hàng của người dùng hiện tại từ GET /cart."""
        from state.auth_state import AuthState
        auth = await self.get_state(AuthState)

        if not auth.token:
            self.cart_items = []
            self.total_price = 0.0
            return

        data, err = await api_client.get("/cart", token=auth.token)
        if err or not isinstance(data, dict):
            if err and "401" in err:
                await auth.logout()
            self.error_message = err or "Không thể tải giỏ hàng."
            return

        items = data.get("items", [])
        for it in items:
            it["product_image"] = resolve_media_url(it.get("product_image"))
            p_price = float(it.get("product_price") or 0.0)
            it["formatted_price"] = f"{p_price:,.0f} đ".replace(",", ".")

        self.cart_items = items
        self.total_price = float(data.get("total_amount", 0.0))
        self.error_message = ""

    async def add_to_cart(self, product_id: str, record_id: Optional[str] = None):
        """Thêm sản phẩm vào giỏ (gắn kèm mã record nếu tìm từ ảnh quét) qua POST /cart/items."""
        from state.auth_state import AuthState
        auth = await self.get_state(AuthState)

        # Nếu chưa đăng nhập, tự động bootstrap session khách để trải nghiệm mượt mà
        if not auth.token:
            await auth.login_dev("customer@system.local")

        payload: Dict[str, Any] = {
            "product_id": product_id,
            "quantity": 1,
        }
        if record_id:
            payload["record_id"] = record_id

        data, err = await api_client.post("/cart/items", json_data=payload, token=auth.token)
        if err:
            if "401" in err:
                await auth.logout()
            self.error_message = err
            return rx.toast(f"Lỗi: {err}", position="top-center")

        await self.fetch_cart()
        return rx.toast("Đã thêm sản phẩm vào giỏ hàng thành công!", position="top-center")

    async def increment_item(self, item_id: str) -> None:
        """Tăng số lượng sản phẩm lên 1."""
        for it in self.cart_items:
            if str(it.get("id")) == str(item_id):
                await self.update_quantity(item_id, int(it.get("quantity", 1)) + 1)
                break

    async def decrement_item(self, item_id: str) -> None:
        """Giảm số lượng sản phẩm đi 1."""
        for it in self.cart_items:
            if str(it.get("id")) == str(item_id):
                await self.update_quantity(item_id, int(it.get("quantity", 1)) - 1)
                break

    async def update_quantity(self, item_id: str, quantity: int) -> None:
        """Cập nhật số lượng mặt hàng qua PUT /cart/items/{item_id}."""
        from state.auth_state import AuthState
        auth = await self.get_state(AuthState)

        if not auth.token:
            return

        if quantity <= 0:
            await self.remove_item(item_id)
            return

        payload = {"quantity": quantity}
        data, err = await api_client.put(f"/cart/items/{item_id}", json_data=payload, token=auth.token)
        if err:
            if "401" in err:
                await auth.logout()
            self.error_message = err
            return

        await self.fetch_cart()

    async def remove_item(self, item_id: str) -> None:
        """Xóa hoàn toàn một món hàng khỏi giỏ qua DELETE /cart/items/{item_id}."""
        from state.auth_state import AuthState
        auth = await self.get_state(AuthState)

        if not auth.token:
            return

        data, err = await api_client.delete(f"/cart/items/{item_id}", token=auth.token)
        if err:
            if "401" in err:
                await auth.logout()
            self.error_message = err
            return

        await self.fetch_cart()

    async def checkout(self):
        """Chuyển đổi giỏ hàng thành đơn hàng mới, kích hoạt phát âm thanh TTS xác nhận."""
        from state.auth_state import AuthState
        auth = await self.get_state(AuthState)

        if not auth.token:
            return rx.toast("Vui lòng đăng nhập trước khi tiến hành thanh toán.", position="top-center")

        if not self.cart_items:
            return rx.toast("Giỏ hàng của bạn đang trống.", position="top-center")

        clean_addr = (self.shipping_address or "").strip()
        clean_phone = (self.phone_number or "").strip()
        if not clean_addr or not clean_phone:
            return rx.toast("Vui lòng nhập đầy đủ địa chỉ giao hàng và số điện thoại.", position="top-center")

        self.is_checking_out = True
        self.error_message = ""

        payload = {
            "shipping_address": clean_addr,
            "phone_number": clean_phone,
        }

        data, err = await api_client.post("/orders/checkout", json_data=payload, token=auth.token, timeout=60.0)
        self.is_checking_out = False

        if err or not isinstance(data, dict):
            if err and "401" in err:
                await auth.logout()
            self.error_message = err or "Thanh toán thất bại."
            return rx.toast(f"Lỗi đặt hàng: {self.error_message}", position="top-center")

        self.last_order_id = str(data.get("id", ""))
        raw_audio = data.get("audio_confirmation_url")
        self.checkout_audio_url = resolve_media_url(raw_audio)
        self.checkout_success = True

        # Xóa rỗng giỏ hàng sau khi đặt thành công
        self.cart_items = []
        self.total_price = 0.0

        return rx.toast("Đặt hàng thành công! Vui lòng lắng nghe xác nhận âm thanh.", position="top-center")
