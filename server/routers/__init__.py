from server.routers.auth import ns_auth
from server.routers.cart import ns_cart
from server.routers.categories import ns_categories
from server.routers.copilot import ns_copilot
from server.routers.detect import ns_detect, ns_static
from server.routers.health import ns_health
from server.routers.media import media_bp, ns_media
from server.routers.mlops import ns_mlops
from server.routers.ocr_records import ns_records
from server.routers.ocr_reviews import ns_reviews
from server.routers.orders import ns_orders
from server.routers.products import ns_products
from server.routers.roles import ns_roles
from server.routers.users import ns_users

all_namespaces = [
    ns_auth,
    ns_detect,
    ns_media,
    ns_static,
    ns_reviews,
    ns_roles,
    ns_users,
    ns_records,
    ns_categories,
    ns_products,
    ns_cart,
    ns_orders,
    ns_health,
    ns_mlops,
    ns_copilot,
]

__all__ = [
    "all_namespaces",
    "media_bp",
    "ns_auth",
    "ns_cart",
    "ns_categories",
    "ns_copilot",
    "ns_detect",
    "ns_health",
    "ns_media",
    "ns_mlops",
    "ns_orders",
    "ns_products",
    "ns_records",
    "ns_reviews",
    "ns_roles",
    "ns_static",
    "ns_users",
]
