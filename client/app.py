import sys
from pathlib import Path
import reflex as rx

CLIENT_DIR = Path(__file__).resolve().parent
if str(CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(CLIENT_DIR))

from pages.index import index
from pages.login import login_page
from pages.admin_dashboard import admin_dashboard_page

app = rx.App()

app.add_page(index, route="/", title="SmartVision Commerce | AI Visual Shopping")
app.add_page(login_page, route="/login", title="Đăng Nhập | SmartVision Store")
app.add_page(admin_dashboard_page, route="/admin", title="Quản Trị Hệ Thống | SmartVision Store")

