from typing import Any, Dict
import reflex as rx
from api.client import api_client


class AuthState(rx.State):
    """Hook quản lý Authentication, JWT Token trong LocalStorage và phân quyền RBAC."""

    # Lưu trữ JWT token vào LocalStorage của trình duyệt với key 'access_token'
    token: str = rx.LocalStorage("", name="access_token")
    current_user: Dict[str, Any] = {}
    is_authenticated: bool = False
    login_error: str = ""
    is_loading: bool = False

    login_email: str = "admin@system.local"
    login_role: int = 1

    @rx.var
    def error_message(self) -> str:
        """Alias cho login_error để tương thích giao diện."""
        return self.login_error

    @rx.var
    def is_admin(self) -> bool:
        """Computed var xác định quyền Admin (Role ID = 1)."""
        return int(self.current_user.get("role_id", 0)) == 1

    def set_email(self, email: str) -> None:
        self.login_email = email

    def set_role(self, role_id: Any) -> None:
        try:
            self.login_role = int(role_id)
        except (ValueError, TypeError):
            self.login_role = 1

    async def login(self):
        """Đăng nhập bằng email và vai trò đã chọn trên form login."""
        return await self.login_dev(username=self.login_email)

    async def dev_login(self, role: int = 1):
        """Đăng nhập nhanh cho dev theo role ID."""
        email = "admin@system.local" if int(role) == 1 else "customer@system.local"
        return await self.login_dev(username=email)

    async def check_auth(self) -> None:
        """Kiểm tra tính hợp lệ của token qua GET /auth/me. Nếu hết hạn thì tự động logout."""
        if not self.token:
            self.is_authenticated = False
            self.current_user = {}
            return

        data, err = await api_client.get("/auth/me", token=self.token)
        if err or not isinstance(data, dict):
            # Server trả về 401 hoặc token không hợp lệ -> xóa token và reset state
            await self.logout()
            return

        self.current_user = data
        self.is_authenticated = True
        self.login_error = ""

    async def login_dev(self, username: str = "admin@system.local", password: str = ""):
        """Đăng nhập môi trường phát triển / admin bypass và lưu token vào LocalStorage."""
        self.is_loading = True
        self.login_error = ""

        clean_username = username.strip()
        email = clean_username if "@" in clean_username else f"{clean_username}@system.local"
        role_id = 1 if "admin" in clean_username.lower() else 2

        payload = {
            "email": email,
            "role_id": role_id,
            "full_name": "Quản Trị Viên" if role_id == 1 else "Khách Hàng",
            "password": password,
        }

        data, err = await api_client.post("/auth/login", json_data=payload)
        self.is_loading = False

        if err or not isinstance(data, dict):
            self.login_error = err or "Đăng nhập thất bại. Vui lòng thử lại."
            return

        self.token = data.get("access_token", "")
        self.current_user = data.get("user", {})
        self.is_authenticated = True
        self.login_error = ""
        return rx.redirect("/")

    async def login_google(self, credential: str):
        """Xác thực qua Google OAuth ID Token."""
        self.is_loading = True
        self.login_error = ""

        data, err = await api_client.post("/auth/google", json_data={"id_token": credential})
        self.is_loading = False

        if err or not isinstance(data, dict):
            self.login_error = err or "Xác thực tài khoản Google không thành công."
            return

        self.token = data.get("access_token", "")
        self.current_user = data.get("user", {})
        self.is_authenticated = True
        self.login_error = ""
        return rx.redirect("/")

    async def logout(self):
        """Hủy phiên đăng nhập, xóa token LocalStorage và điều hướng về trang chủ."""
        if self.token:
            await api_client.post("/auth/logout", token=self.token)

        self.token = ""
        self.current_user = {}
        self.is_authenticated = False
        self.login_error = ""
        return rx.redirect("/")
