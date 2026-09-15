from server.routers.detection import router as detection_router
from server.routers.ocr_records import router as ocr_records_router
from server.routers.ocr_reviews import router as ocr_reviews_router
from server.routers.roles import router as roles_router
from server.routers.users import router as users_router

__all__ = [
    "roles_router",
    "users_router",
    "ocr_records_router",
    "ocr_reviews_router",
    "detection_router",
]

