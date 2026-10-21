import io
from flask import Blueprint, jsonify, request, send_file
from app.services.document_service import (
    process_and_save_document,
    get_document_by_id,
    list_documents,
    delete_document,
)
from app.validators.document_validator import validate_document_upload

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")


@documents_bp.route("/upload", methods=["POST"])
def upload_document():
    """
    Upload và xử lý tài liệu (PDF / TXT) hoàn toàn trong RAM
    ---
    tags:
      - Documents
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
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    try:
        document = process_and_save_document(user_id=user_id, file_storage=file_storage)
        doc_dict = document.to_dict()
        doc_dict["message"] = "Upload và xử lý tài liệu thành công"
        doc_dict["document"] = document.to_dict()
        return jsonify(doc_dict), 201
    except Exception as exc:
        return jsonify({"error": f"Lỗi xử lý tài liệu: {str(exc)}"}), 500


@documents_bp.route("/<int:doc_id>", methods=["GET"])
def get_document(doc_id: int):
    """
    Xem metadata và text trích xuất của Document (hoặc tải về file raw BLOB)
    ---
    tags:
      - Documents
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID của tài liệu
      - name: download
        in: query
        type: boolean
        required: false
        description: Nếu là true, tải trực tiếp dữ liệu binary từ cột BLOB
    responses:
      200:
        description: Metadata và extracted_text của tài liệu
      404:
        description: Không tìm thấy tài liệu
    """
    document = get_document_by_id(doc_id)
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

    return jsonify(document.to_dict()), 200


@documents_bp.route("", methods=["GET"])
def get_all_documents():
    """Lấy danh sách tài liệu đã upload"""
    user_id_raw = request.args.get("user_id")
    user_id = int(user_id_raw) if user_id_raw and user_id_raw.isdigit() else None
    documents = list_documents(user_id=user_id)
    return jsonify([doc.to_dict() for doc in documents]), 200


@documents_bp.route("/<int:doc_id>", methods=["DELETE"])
def remove_document(doc_id: int):
    """Xóa tài liệu theo ID"""
    success = delete_document(doc_id)
    if not success:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404
    return jsonify({"message": f"Đã xóa tài liệu ID {doc_id} thành công"}), 200
