from server.crud.base import CRUDBase
from server.crud.crud_role import CRUDRole, crud_role
from server.crud.crud_user import CRUDUser, crud_user
from server.crud.crud_ocr_record import CRUDOCRRecord, crud_ocr_record
from server.crud.crud_ocr_review import CRUDOCRReview, crud_ocr_review

__all__ = [
    "CRUDBase",
    "CRUDRole",
    "crud_role",
    "CRUDUser",
    "crud_user",
    "CRUDOCRRecord",
    "crud_ocr_record",
    "CRUDOCRReview",
    "crud_ocr_review",
]

