from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from nicegui import app, ui

logger = logging.getLogger(__name__)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Trích xuất thông tin người dùng từ NiceGUI app.storage.user."""
    try:
        user = app.storage.user.get("user", None)
        if isinstance(user, dict) and user:
            return user
        return None
    except Exception:
        return None


def set_current_user(
    user: Optional[Dict[str, Any]], token: Optional[str] = None
) -> None:
    """Ghi hoặc xóa phiên đăng nhập của người dùng vào session storage."""
    try:
        if user:
            app.storage.user["user"] = user
            app.storage.user["is_authenticated"] = True
            if token:
                app.storage.user["token"] = token
        else:
            app.storage.user.pop("user", None)
            app.storage.user.pop("token", None)
            app.storage.user["is_authenticated"] = False
    except Exception as err:
        logger.warning("Không thể cập nhật session storage: %s", err)


def is_authenticated() -> bool:
    """Kiểm tra trạng thái xác thực phiên làm việc hiện tại."""
    try:
        user = get_current_user()
        if user is not None:
            return True
        return bool(app.storage.user.get("is_authenticated", False))
    except Exception:
        return False


def require_auth() -> bool:
    """Route Guard cho các trang Private/Protected (/decks, /study, /profile).
    
    Điều hướng về /login nếu người dùng chưa đăng nhập.
    """
    if not is_authenticated():
        from components.layout import show_toast
        show_toast("Vui lòng đăng nhập để tiếp tục", "warning")
        ui.navigate.to("/login")
        return False
    return True


def redirect_if_authenticated(target: str = "/decks") -> bool:
    """Route Guard cho trang Guest (/login, /register).
    
    Tự động chuyển hướng về trang /decks nếu người dùng đã có phiên xác thực.
    """
    if is_authenticated():
        ui.navigate.to(target)
        return True
    return False


def logout() -> None:
    """Đăng xuất người dùng, dọn dẹp storage và điều hướng về trang đăng nhập."""
    from components.layout import show_toast
    set_current_user(None)
    show_toast("Đã đăng xuất thành công", "positive")
    ui.navigate.to("/login")

