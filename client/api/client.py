from typing import Any, Dict, Optional, Tuple
import httpx
from api.config import API_BASE_URL, DEFAULT_TIMEOUT, SERVER_URL


def resolve_media_url(url_or_path: Optional[str]) -> str:
    """Chuyển đổi đường dẫn media cục bộ của server thành URL đầy đủ cho giao diện trình duyệt."""
    if not url_or_path:
        return ""
    if url_or_path.startswith(("http://", "https://")):
        return url_or_path
    clean_path = url_or_path.lstrip("/")
    return f"{SERVER_URL}/{clean_path}"


class ApiClient:
    """Async Network Service bọc thư viện httpx, chuẩn hóa phản hồi và xử lý ngoại lệ."""

    def __init__(self, base_url: str = API_BASE_URL, default_timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout

    def _build_url(self, endpoint: str) -> str:
        """Ghép nối endpoint với base_url an toàn."""
        if endpoint.startswith(("http://", "https://")):
            return endpoint
        clean_endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{clean_endpoint}"

    def _prepare_headers(
        self,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
    ) -> Dict[str, str]:
        """Tạo header mặc định và inject Bearer Token nếu có."""
        final_headers = {"Accept": "application/json"}
        if token:
            clean_token = token.strip().replace('"', "")
            if clean_token:
                final_headers["Authorization"] = f"Bearer {clean_token}"
        if headers:
            final_headers.update(headers)
        return final_headers

    async def _handle_response(self, response: httpx.Response) -> Tuple[Any, Optional[str]]:
        """Phân tích nội dung JSON và chuẩn hóa kết quả về dạng (data, error_message)."""
        content_type = response.headers.get("content-type", "")
        is_json = content_type.startswith("application/json")
        payload = response.json() if is_json else response.text

        if response.is_success:
            return payload, None

        # Trích xuất thông báo lỗi từ payload của Flask-RESTX
        if isinstance(payload, dict):
            error_msg = payload.get("detail") or payload.get("message") or response.text
        else:
            error_msg = str(payload)

        # Đánh dấu rõ mã lỗi 401 để tầng State tự động xử lý hủy token
        if response.status_code == 401:
            return None, f"401 Unauthorized: {error_msg}"

        return None, f"Lỗi HTTP {response.status_code}: {error_msg}"

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[Any, Optional[str]]:
        """Thực hiện HTTP GET request bất đồng bộ."""
        target_url = self._build_url(url)
        req_headers = self._prepare_headers(headers, token)

        try:
            async with httpx.AsyncClient(timeout=timeout or self.default_timeout) as client:
                res = await client.get(target_url, params=params, headers=req_headers)
                return await self._handle_response(res)
        except httpx.ConnectTimeout:
            return None, "Không thể kết nối đến Gateway quá thời gian chờ (ConnectTimeout)."
        except httpx.ReadTimeout:
            return None, "Máy chủ phản hồi quá thời gian cho phép (ReadTimeout)."
        except httpx.ConnectError:
            return None, "Không thể kết nối đến máy chủ backend (Server Offline)."
        except httpx.HTTPStatusError as exc:
            return None, f"Lỗi trạng thái HTTP: {str(exc)}"
        except Exception as exc:
            return None, f"Lỗi kết nối mạng: {str(exc)}"

    async def post(
        self,
        url: str,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[Any, Optional[str]]:
        """Thực hiện HTTP POST request bất đồng bộ hỗ trợ JSON, Form Data và Multipart Files."""
        target_url = self._build_url(url)
        req_headers = self._prepare_headers(headers, token)

        try:
            async with httpx.AsyncClient(timeout=timeout or self.default_timeout) as client:
                res = await client.post(
                    target_url,
                    json=json_data,
                    data=data,
                    files=files,
                    headers=req_headers,
                )
                return await self._handle_response(res)
        except httpx.ConnectTimeout:
            return None, "Không thể kết nối đến Gateway quá thời gian chờ (ConnectTimeout)."
        except httpx.ReadTimeout:
            return None, "Máy chủ xử lý tác vụ quá lâu (ReadTimeout)."
        except httpx.ConnectError:
            return None, "Không thể kết nối đến máy chủ backend (Server Offline)."
        except httpx.HTTPStatusError as exc:
            return None, f"Lỗi trạng thái HTTP: {str(exc)}"
        except Exception as exc:
            return None, f"Lỗi kết nối mạng: {str(exc)}"

    async def put(
        self,
        url: str,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[Any, Optional[str]]:
        """Thực hiện HTTP PUT request bất đồng bộ."""
        target_url = self._build_url(url)
        req_headers = self._prepare_headers(headers, token)

        try:
            async with httpx.AsyncClient(timeout=timeout or self.default_timeout) as client:
                res = await client.put(
                    target_url,
                    json=json_data,
                    data=data,
                    headers=req_headers,
                )
                return await self._handle_response(res)
        except httpx.ConnectTimeout:
            return None, "Kết nối quá thời gian chờ (ConnectTimeout)."
        except httpx.ReadTimeout:
            return None, "Máy chủ phản hồi quá thời gian (ReadTimeout)."
        except httpx.ConnectError:
            return None, "Không thể kết nối đến máy chủ backend (Server Offline)."
        except httpx.HTTPStatusError as exc:
            return None, f"Lỗi trạng thái HTTP: {str(exc)}"
        except Exception as exc:
            return None, f"Lỗi kết nối mạng: {str(exc)}"

    async def delete(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[Any, Optional[str]]:
        """Thực hiện HTTP DELETE request bất đồng bộ."""
        target_url = self._build_url(url)
        req_headers = self._prepare_headers(headers, token)

        try:
            async with httpx.AsyncClient(timeout=timeout or self.default_timeout) as client:
                res = await client.delete(target_url, params=params, headers=req_headers)
                return await self._handle_response(res)
        except httpx.ConnectTimeout:
            return None, "Kết nối quá thời gian chờ (ConnectTimeout)."
        except httpx.ReadTimeout:
            return None, "Máy chủ phản hồi quá thời gian (ReadTimeout)."
        except httpx.ConnectError:
            return None, "Không thể kết nối đến máy chủ backend (Server Offline)."
        except httpx.HTTPStatusError as exc:
            return None, f"Lỗi trạng thái HTTP: {str(exc)}"
        except Exception as exc:
            return None, f"Lỗi kết nối mạng: {str(exc)}"


# Global Singleton Instance cho toàn bộ ứng dụng
api_client = ApiClient()
