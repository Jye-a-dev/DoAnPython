"""
documents.py — Documents CRUD API endpoints (Tag: Documents).
Quản lý thực thể: documents (Table 5) lưu trữ trực tiếp file nhị phân BLOB trong DB.
"""

from __future__ import annotations

import hashlib
import io
import os
from flask import Blueprint, jsonify, request, send_file
import pypdf
from sqlalchemy.orm import defer
from app.core.database import db
from app.models.document import Document
from app.validators.document_validator import validate_document_upload

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")


@documents_bp.route("/upload", methods=["POST"])
def upload_document():
    """
    Upload và xử lý tài liệu in-memory BLOB (POST /api/documents/upload)
    ---
    tags:
      - Documents
    summary: Nhận file PDF/TXT nạp vào RAM qua io.BytesIO, tính SHA-256, parse text, lưu trực tiếp BLOB vào DB
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: File tài liệu (PDF hoặc TXT, tối đa 10MB)
      - name: user_id
        in: formData
        type: integer
        required: true
        description: ID của người dùng sở hữu tài liệu
    responses:
      201:
        description: Upload và trích xuất text thành công
      400:
        description: File không hợp lệ, rỗng hoặc vượt quá dung lượng
      409:
        description: Trùng lặp nội dung file (content_hash đã tồn tại)
      500:
        description: Lỗi máy chủ khi xử lý file
    """
    if "file" not in request.files:
        return (
            jsonify(
                {"error": "Không tìm thấy trường 'file' trong multipart/form-data"}
            ),
            400,
        )

    file_storage = request.files["file"]
    user_id_raw = request.form.get("user_id")

    if not user_id_raw:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400

    try:
        user_id = int(user_id_raw)
        if user_id <= 0:
            return jsonify({"error": "Trường 'user_id' phải là số nguyên dương"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Trường 'user_id' phải là số nguyên"}), 400

    is_valid, error_msg, file_bytes, _ = validate_document_upload(file_storage)
    if not is_valid or file_bytes is None:
        return jsonify({"error": error_msg or "Dữ liệu file không hợp lệ"}), 400

    filename = getattr(file_storage, "filename", None) or "document.txt"
    ext = os.path.splitext(filename)[1].lower().lstrip(".") or "txt"
    file_size = len(file_bytes)

    # 1. Tính mã băm SHA-256 và kiểm tra chống trùng lặp theo schema UNIQUE (content_hash)
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    existing_doc = Document.query.filter_by(content_hash=content_hash).first()
    if existing_doc:
        return (
            jsonify(
                {
                    "error": "Tài liệu này đã tồn tại trong cơ sở dữ liệu (trùng content_hash)",
                    "existing_document_id": existing_doc.id,
                    "content_hash": content_hash,
                }
            ),
            409,
        )

    # 2. Parse extracted_text trực tiếp trong RAM qua io.BytesIO
    extracted_text = ""
    if ext == "pdf":
        try:
            pdf_stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_stream)
            page_texts = [p.extract_text() or "" for p in reader.pages]
            extracted_text = "\n\n".join(
                t.strip() for t in page_texts if t.strip()
            ).strip()
        except Exception as exc:
            extracted_text = f"[PDF Extraction Error: {str(exc)}]"
    else:
        extracted_text = file_bytes.decode("utf-8", errors="ignore").strip()

    # 3. Lưu trực tiếp vào cột BLOB file_blob mà không ghi file cục bộ
    document = Document(
        user_id=user_id,
        filename=filename,
        file_type=ext,
        file_size_bytes=file_size,
        file_blob=file_bytes,
        extracted_text=extracted_text,
        content_hash=content_hash,
    )
    try:
        db.session.add(document)
        db.session.commit()
        doc_dict = document.to_dict()
        doc_dict["message"] = "Upload và lưu trữ BLOB tài liệu thành công"
        return jsonify(doc_dict), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi lưu trữ tài liệu: {str(exc)}"}), 500


@documents_bp.route("", methods=["GET"])
def list_all_documents():
    """
    Lấy danh sách tài liệu tối ưu RAM (GET /api/documents)
    ---
    tags:
      - Documents
    summary: Lấy danh sách tài liệu (id, filename, file_type, file_size_bytes, content_hash, created_at - không tải file_blob)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc tài liệu theo ID người dùng
    responses:
      200:
        description: Danh sách metadata tài liệu
      500:
        description: Lỗi truy vấn
    """
    user_id_raw = request.args.get("user_id")
    user_id = int(user_id_raw) if user_id_raw and user_id_raw.isdigit() else None

    # Defer loading file_blob column để tiết kiệm RAM
    query = Document.query.options(defer(getattr(Document, "file_blob")))
    if user_id is not None:
        query = query.filter_by(user_id=user_id)

    documents = query.order_by(Document.created_at.desc()).all()
    return jsonify([doc.to_dict(include_blob=False) for doc in documents]), 200


@documents_bp.route("/<int:doc_id>", methods=["GET"])
def get_document_by_id_endpoint(doc_id: int):
    """
    Xem metadata và extracted_text của tài liệu (GET /api/documents/{id})
    ---
    tags:
      - Documents
    summary: Xem metadata và text trích xuất của tài liệu (hỗ trợ ?download=true tải raw BLOB)
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID tài liệu
      - name: download
        in: query
        type: boolean
        required: false
        description: Nếu true, stream trực tiếp binary file_blob
    responses:
      200:
        description: Metadata và text hoặc file stream
      404:
        description: Không tìm thấy tài liệu
    """
    document = db.session.get(Document, doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

    is_download = request.args.get("download", "").lower() in ["true", "1"]
    if is_download:
        mimetype = (
            "application/pdf"
            if document.file_type == "pdf"
            else "text/plain; charset=utf-8"
        )
        return send_file(
            io.BytesIO(document.file_blob),
            mimetype=mimetype,
            as_attachment=True,
            download_name=document.filename,
        )

    return jsonify(document.to_dict(include_blob=False)), 200


@documents_bp.route("/<int:doc_id>/download", methods=["GET"])
def download_document_blob_endpoint(doc_id: int):
    """
    Tải lại file nhị phân gốc từ cột file_blob trong DB (GET /api/documents/{id}/download)
    ---
    tags:
      - Documents
    summary: Tải lại file nhị phân gốc được stream trực tiếp từ cột file_blob trong DB
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID tài liệu cần tải
    responses:
      200:
        description: Stream tệp nhị phân gốc thành công
      404:
        description: Không tìm thấy tài liệu
    """
    document = db.session.get(Document, doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

    mimetype = (
        "application/pdf"
        if document.file_type == "pdf"
        else "text/plain; charset=utf-8"
    )
    return send_file(
        io.BytesIO(document.file_blob),
        mimetype=mimetype,
        as_attachment=True,
        download_name=document.filename,
    )


@documents_bp.route("/<int:doc_id>", methods=["DELETE"])
def delete_document_endpoint(doc_id: int):
    """
    Xóa tài liệu khỏi DB (DELETE /api/documents/{id})
    ---
    tags:
      - Documents
    summary: Xóa tài liệu khỏi DB (các card tạo từ doc này sẽ set document_id = NULL theo ON DELETE SET NULL)
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID tài liệu cần xóa
    responses:
      200:
        description: Đã xóa tài liệu thành công
      404:
        description: Không tìm thấy tài liệu
      500:
        description: Lỗi máy chủ khi xóa
    """
    document = db.session.get(Document, doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

    try:
        db.session.delete(document)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Đã xóa tài liệu ID {doc_id} thành công (các thẻ liên quan đã chuyển document_id = NULL)"
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa tài liệu: {str(exc)}"}), 500
