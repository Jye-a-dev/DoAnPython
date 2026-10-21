import io
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Cấu hình sys.path đảm bảo import đúng thư mục server và pipeline
_TEST_DIR = Path(__file__).resolve().parent
_SERVER_DIR = _TEST_DIR.parent
_ROOT_DIR = _SERVER_DIR.parent
for _p in [str(_SERVER_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pypdf
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from app.main import create_app
from app.core.database import db
from app.models.user import User
from app.models.document import Document
from app.models.flashcard import Deck, Card, Tag, card_tags
from app.models.study import AIGenerationLog


def _generate_valid_in_memory_pdf(text: str = "Software Architecture and Engineering Design Principles") -> io.BytesIO:
    """
    Sinh file PDF hợp lệ chuẩn cấu trúc trong RAM với con trỏ xref chính xác,
    đáp ứng trích xuất text trực tiếp từ buffer mà không ghi xuống đĩa cứng.
    """
    stream_content = f"BT\n/F1 12 Tf\n100 700 Td\n({text}) Tj\nET\n".encode("latin-1")
    stream_len = len(stream_content)

    parts = [
        b"%PDF-1.4\n",
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        f"5 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin-1") + stream_content + b"endstream\nendobj\n",
    ]

    offsets = [0]
    cur = 0
    for p in parts[:-1]:
        cur += len(p)
        offsets.append(cur)

    cur += len(parts[-1])
    xref_pos = cur

    xref = [f"xref\n0 {len(parts)}\n".encode("latin-1"), b"0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("latin-1"))

    trailer = f"trailer\n<< /Size {len(parts)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
    return io.BytesIO(b"".join(parts) + b"".join(xref) + trailer)


@pytest.fixture
def app():
    """
    Khởi tạo Flask app cấu hình Testing với Dynamic SQLite in-memory,
    StaticPool chia sẻ kết nối và cưỡng chế PRAGMA foreign_keys=ON.
    """
    flask_app = create_app()
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with flask_app.app_context():
        db.create_all()

        # Kiểm tra xác nhận PRAGMA foreign_keys=ON trên SQLite connection
        fk_enabled = db.session.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk_enabled == 1, "PRAGMA foreign_keys=ON bắt buộc phải được kích hoạt!"

        # Khởi tạo User dùng chung cho các test cases
        user = User(
            username="qa_architect",
            email="qa@eduflash.ai",
            password_hash="argon2_mock_hash_for_testing",
        )
        db.session.add(user)
        db.session.commit()

        yield flask_app

        # Dọn dẹp hermetic sau mỗi test case
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(app):
    """Fixture cung cấp SQLAlchemy database session độc lập."""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def client(app):
    """Fixture cung cấp Flask Test Client kết nối tới in-memory database."""
    return app.test_client()


@pytest.fixture
def test_user(db_session):
    """Lấy bản ghi User được khởi tạo sẵn trong session."""
    return db_session.query(User).filter_by(username="qa_architect").one()


def test_e2e_document_upload_blob_and_zero_disk(client, db_session, test_user):
    """
    Test 1: Upload PDF mẫu & Zero-Disk File Assertion.
    - Đọc từ io.BytesIO buffer thẳng vào trường BLOB của bảng documents.
    - Xác thực trích xuất text tự động.
    - Đảm bảo snapshot hệ thống tệp không phát sinh bất kỳ file rác nào trên ổ đĩa.
    """
    workspace_dir = Path.cwd()

    def snapshot_disk_files():
        file_set = set()
        for root, dirs, files in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"__pycache__", "instance"}]
            for f in files:
                file_set.add(os.path.join(root, f))
        return file_set

    disk_snapshot_before = snapshot_disk_files()

    sample_text = "Software Architecture and Engineering Design Principles"
    pdf_buffer = _generate_valid_in_memory_pdf(text=sample_text)
    buffer_bytes = pdf_buffer.getvalue()
    buffer_size = len(buffer_bytes)

    multipart_data = {
        "user_id": test_user.id,
        "file": (pdf_buffer, "spec_document.pdf", "application/pdf"),
    }

    response = client.post(
        "/api/documents/upload",
        data=multipart_data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 201, f"Upload thất bại: {response.get_json()}"
    res_data = response.get_json()
    doc_id = res_data.get("id") or (res_data.get("document", {}).get("id"))
    assert doc_id is not None, "Endpoint upload không trả về doc_id hợp lệ"

    # 1. Truy vấn database kiểm tra tính toàn vẹn dữ liệu BLOB và text trích xuất
    saved_doc = db_session.get(Document, doc_id)
    assert saved_doc is not None, "Bản ghi Document không tồn tại trong database"
    assert saved_doc.file_blob is not None, "Trường file_blob bị NULL"
    assert len(saved_doc.file_blob) == buffer_size, "Kích thước BLOB không khớp với buffer gốc"
    assert saved_doc.file_blob == buffer_bytes, "Dữ liệu bytes trong BLOB bị sai lệch"
    assert saved_doc.extracted_text is not None, "extracted_text bị NULL"
    assert sample_text in saved_doc.extracted_text, "Nội dung text PDF không được trích xuất chính xác"

    # 2. Kiểm tra Zero-Disk Storage: Không phát sinh bất kỳ file mới nào trên ổ cứng
    disk_snapshot_after = snapshot_disk_files()
    unexpected_files = disk_snapshot_after - disk_snapshot_before
    assert len(unexpected_files) == 0, f"Phát hiện file đệm/tạm bị ghi vào ổ đĩa: {unexpected_files}"


def test_e2e_ai_generate_flashcards_and_audit_logging(client, db_session, test_user):
    """
    Test 2: Trigger AI Sinh Flashcard & Log Metric.
    - Kích hoạt pipeline sinh thẻ từ doc_id qua endpoint POST /api/cards/generate.
    - Giả lập inference phản hồi chuẩn xác mà không cần GPU hoặc model tải chậm.
    - Xác thực thẻ lưu vào bảng cards với trường front/back và log lưu vào ai_generation_logs.
    """
    # Khởi tạo Document có nội dung text hợp lệ
    document = Document(
        user_id=test_user.id,
        filename="microservices_design.pdf",
        file_type="pdf",
        file_blob=b"%PDF-1.4 mock binary stream",
        extracted_text="Microservices architecture structures an application as a collection of loosely coupled services.",
        content_hash="hash_microservices_spec_2026",
    )
    db_session.add(document)

    deck = Deck(
        user_id=test_user.id,
        title="Software Engineering Patterns",
        description="Core principles of software design",
    )
    db_session.add(deck)
    db_session.commit()

    mock_generated_qa = [
        {
            "question": "What is a microservices architecture?",
            "answer": "An architecture structuring an application as loosely coupled, independently deployable services.",
            "front": "What is a microservices architecture?",
            "back": "An architecture structuring an application as loosely coupled, independently deployable services.",
        },
        {
            "question": "How are services coupled in microservices?",
            "answer": "They are loosely coupled.",
            "front": "How are services coupled in microservices?",
            "back": "They are loosely coupled.",
        },
    ]

    # Giả lập pipeline inference HTTP response từ AI Pipeline Microservice
    with patch("app.services.ai_service._post_json", return_value={"status": "success", "cards": mock_generated_qa}):
        generate_payload = {
            "doc_id": document.id,
            "deck_id": deck.id,
            "user_id": test_user.id,
        }
        response = client.post(
            "/api/cards/generate",
            json=generate_payload,
        )

        assert response.status_code == 201, f"Sinh thẻ thất bại: {response.get_json()}"
        res_json = response.get_json()
        assert res_json.get("status") == "SUCCESS"
        assert res_json.get("cards_generated") == 2

    # 1. Xác thực bảng cards
    persisted_cards = db_session.query(Card).filter_by(document_id=document.id).all()
    assert len(persisted_cards) == 2, "Số lượng card lưu vào database không khớp"

    for card in persisted_cards:
        assert card.deck_id == deck.id
        assert card.document_id == document.id
        assert len(card.front.strip()) > 0
        assert len(card.back.strip()) > 0
        assert card.question == card.front
        assert card.answer == card.back

    # 2. Xác thực bảng ai_generation_logs
    audit_log = db_session.query(AIGenerationLog).filter_by(document_id=document.id).first()
    assert audit_log is not None, "Không tìm thấy telemetry log trong bảng ai_generation_logs"
    assert audit_log.status == "SUCCESS", "Trạng thái log phải là SUCCESS"
    assert audit_log.document_id == document.id
    assert audit_log.deck_id == deck.id
    assert audit_log.cards_generated == 2
    assert audit_log.inference_time_seconds >= 0.0
    assert audit_log.prompt_tokens > 0
    assert audit_log.completion_tokens > 0
    assert audit_log.error_message is None


def test_e2e_relational_queries_deck_card_tag_document(client, db_session, test_user):
    """
    Test 3: Query Toàn vẹn Dữ liệu Quan hệ (Deck -> Card -> Tag -> Document).
    - Tạo quan hệ 3NF hoàn chỉnh: Deck chứa Cards, Card trỏ về Document nguồn và liên kết Tags (M:N).
    - Thực thi query quan hệ sâu qua SQLAlchemy ORM Eager Loading và Join Query.
    - Kiểm tra cưỡng chế khóa ngoại SQLite (PRAGMA foreign_keys=ON) và xử lý Cascade.
    """
    # 1. Thiết lập kịch bản dữ liệu hoàn chỉnh liên thông
    document = Document(
        user_id=test_user.id,
        filename="database_internals.pdf",
        file_type="pdf",
        file_blob=b"%PDF-1.4 relational db bytes",
        extracted_text="Relational databases enforce referential integrity with foreign key constraints.",
        content_hash="hash_database_internals_relational_3nf",
    )
    deck = Deck(
        user_id=test_user.id,
        title="Database Systems",
        description="Relational database concepts and SQL internals",
    )
    tag_backend = Tag(user_id=test_user.id, name="backend")
    tag_database = Tag(user_id=test_user.id, name="database")

    card = Card(
        deck=deck,
        document=document,
        question="Which pragma enables foreign key enforcement in SQLite?",
        answer="PRAGMA foreign_keys = ON;",
        difficulty="hard",
    )
    card.tags.extend([tag_backend, tag_database])

    db_session.add_all([document, deck, tag_backend, tag_database, card])
    db_session.commit()

    # 2. Thực thi Eager Load qua SQLAlchemy ORM (joinedload + selectinload)
    loaded_deck = (
        db_session.query(Deck)
        .filter(Deck.id == deck.id)
        .options(
            joinedload(Deck.cards).joinedload(Card.document),
            joinedload(Deck.cards).selectinload(Card.tags),
        )
        .one()
    )

    assert len(loaded_deck.cards) == 1
    retrieved_card = loaded_deck.cards[0]
    assert retrieved_card.document is not None
    assert retrieved_card.document.id == document.id
    assert retrieved_card.document.filename == "database_internals.pdf"
    assert {t.name for t in retrieved_card.tags} == {"backend", "database"}

    # 3. Duyệt ngược từ Tag tới Deck và Document qua quan hệ M:N
    queried_tag = db_session.query(Tag).filter_by(name="backend").one()
    assert len(queried_tag.cards) == 1
    assert queried_tag.cards[0].deck.id == deck.id
    assert queried_tag.cards[0].document.id == document.id

    # 4. Thực thi Explicit Multi-Table JOIN Query
    join_results = (
        db_session.query(
            Deck.title.label("deck_title"),
            Card.question.label("card_question"),
            Tag.name.label("tag_name"),
            Document.filename.label("doc_filename"),
        )
        .join(Card, Deck.id == Card.deck_id)
        .join(card_tags, Card.id == card_tags.c.card_id)
        .join(Tag, card_tags.c.tag_id == Tag.id)
        .join(Document, Card.document_id == Document.id)
        .filter(Deck.id == deck.id)
        .all()
    )

    assert len(join_results) == 2, "Phải có đúng 2 hàng tương ứng với 2 Tags liên kết qua card_tags"
    for row in join_results:
        assert row.deck_title == "Database Systems"
        assert row.card_question == "Which pragma enables foreign key enforcement in SQLite?"
        assert row.doc_filename == "database_internals.pdf"
    assert {r.tag_name for r in join_results} == {"backend", "database"}

    # 5. Kiểm tra tính toàn vẹn khóa ngoại (Foreign Key constraint violation)
    orphan_card = Card(
        deck_id=999999,  # deck_id không tồn tại trong DB
        document_id=document.id,
        question="Orphan card question?",
        answer="Must fail due to foreign key constraint violation",
    )
    db_session.add(orphan_card)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 6. Kiểm tra tính toàn vẹn khi Cascade Delete: xóa Deck sẽ xóa Card nhưng bảo toàn Document và Tag
    deck_id = deck.id
    card_id = retrieved_card.id
    doc_id = document.id

    deck_to_delete = db_session.get(Deck, deck_id)
    db_session.delete(deck_to_delete)
    db_session.commit()

    assert db_session.get(Deck, deck_id) is None, "Deck chưa bị xóa"
    assert db_session.get(Card, card_id) is None, "Card chưa bị xóa cascade theo Deck"
    assert db_session.get(Document, doc_id) is not None, "Document không được bị xóa khi xóa Deck"
    assert db_session.query(Tag).filter_by(name="backend").first() is not None, "Tag không được bị xóa"
