from typing import Any, Dict, List
import reflex as rx
from api.client import api_client, resolve_media_url
from api.config import API_BASE_URL


class DetectState(rx.State):
    """Hook quản lý Camera, tải ảnh và nhận diện vật thể AI qua YOLOv8."""

    is_scanning: bool = False
    last_record_id: str = ""
    annotated_image_url: str = ""
    audio_url: str = ""
    summary_text: str = ""
    detected_objects: List[Dict[str, Any]] = []
    error_message: str = ""
    is_modal_open: bool = False

    def open_modal(self) -> None:
        self.is_modal_open = True
        self.error_message = ""

    def close_modal(self) -> None:
        self.is_modal_open = False

    def clear_scan(self) -> None:
        """Đặt lại toàn bộ trạng thái phiên quét."""
        self.is_scanning = False
        self.last_record_id = ""
        self.annotated_image_url = ""
        self.audio_url = ""
        self.summary_text = ""
        self.detected_objects = []
        self.error_message = ""

    async def upload_and_detect(self, files: List[rx.UploadFile]) -> None:
        """Xử lý tải file ảnh lên POST /detect, nhận diện nhãn YOLO và kích hoạt Visual Search."""
        if not files:
            self.error_message = "Vui lòng chọn hoặc chụp ảnh để tiến hành nhận diện."
            return

        self.is_scanning = True
        self.error_message = ""
        file = files[0]

        try:
            # Đọc byte stream bất đồng bộ theo chuẩn Reflex v0.6+
            file_bytes = await file.read()
            filename = getattr(file, "name", "camera_capture.jpg") or "camera_capture.jpg"
            content_type = getattr(file, "content_type", "image/jpeg") or "image/jpeg"

            # Tự động lấy token nếu người dùng đã đăng nhập để gán quyền sở hữu record
            from state.auth_state import AuthState
            auth = await self.get_state(AuthState)

            data, err = await api_client.post(
                "/detect",
                files={"image": (filename, file_bytes, content_type)},
                token=auth.token,
                timeout=90.0,
            )

            if err or not isinstance(data, dict):
                self.error_message = err or "Không thể xử lý nhận dạng hình ảnh qua AI."
                return

            record_id = str(data.get("id", ""))
            self.last_record_id = record_id
            self.summary_text = data.get("summary", "")
            self.detected_objects = data.get("objects", [])

            # Gán URL streaming media trực tiếp từ server database BLOB
            raw_annotated = data.get("annotated_image_url")
            self.annotated_image_url = (
                resolve_media_url(raw_annotated)
                if raw_annotated
                else f"{API_BASE_URL}/media/records/{record_id}/image"
            )

            raw_audio = data.get("audio_url")
            self.audio_url = (
                resolve_media_url(raw_audio)
                if raw_audio
                else f"{API_BASE_URL}/media/records/{record_id}/audio"
            )

            # Tự động gọi ProductState.match_from_scan để tìm sản phẩm trùng khớp nhãn
            if record_id:
                from state.product_state import ProductState
                prod_state = await self.get_state(ProductState)
                await prod_state.match_from_scan(record_id)

        except Exception as exc:
            self.error_message = f"Lỗi hệ thống khi tải ảnh: {str(exc)}"
        finally:
            self.is_scanning = False
