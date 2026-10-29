"""
test_features_suites.py — Kiểm thử các tính năng mới: Heatmap, Deck IO (Export/Import), Personal Notes.
"""

import io
from app.core.database import db
from app.models.flashcard import Card, Deck
from app.models.study import StudyReview, StudySession
from app.models.user import User


def setup_deck_and_user():
    u = User(username="testdev", email="testdev@eduflash.ai", password_hash="hash")
    db.session.add(u)
    db.session.commit()
    d = Deck(user_id=u.id, title="Python Advanced")
    db.session.add(d)
    db.session.commit()
    return u, d


def test_streak_heatmap(client, app):
    with app.app_context():
        u, d = setup_deck_and_user()
        c = Card(
            deck_id=d.id, question="What is GIL?", answer="Global Interpreter Lock"
        )
        db.session.add(c)
        db.session.commit()
        s = StudySession(user_id=u.id, deck_id=d.id)
        db.session.add(s)
        db.session.commit()
        r = StudyReview(session_id=s.id, card_id=c.id, user_id=u.id, review_rating=4)
        db.session.add(r)
        db.session.commit()
        today_str = r.reviewed_at.strftime("%Y-%m-%d")

        res = client.get(f"/api/analytics/streak-heatmap?user_id={u.id}")
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, dict)
        assert today_str in data
        assert data[today_str]["review_count"] >= 1
        assert data[today_str]["level"] >= 1


def test_card_personal_notes(client, app):
    with app.app_context():
        u, d = setup_deck_and_user()
        c = Card(deck_id=d.id, question="Q1", answer="A1", personal_notes="Old Note")
        db.session.add(c)
        db.session.commit()

        res = client.patch(
            f"/api/cards/{c.id}/notes", json={"personal_notes": "New Mnemonic 123"}
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["personal_notes"] == "New Mnemonic 123"

        # Đảm bảo question/answer không bị thay đổi
        card_db = db.session.get(Card, c.id)
        assert card_db is not None
        assert card_db.question == "Q1"
        assert card_db.answer == "A1"
        assert card_db.personal_notes == "New Mnemonic 123"


def test_deck_import_and_export(client, app):
    with app.app_context():
        u, d = setup_deck_and_user()
        raw_text = "Question\tAnswer\tPersonal Notes\nFlask Port\tPort 3000\tBackend\nNiceGUI Port\tPort 5000\tFrontend\n"
        res_import = client.post(f"/api/decks/{d.id}/import", json={"text": raw_text})
        assert res_import.status_code == 201
        data_import = res_import.get_json()
        assert data_import["created_count"] == 2

        # Export CSV
        res_csv = client.get(f"/api/decks/{d.id}/export?format=csv")
        assert res_csv.status_code == 200
        assert b"Flask Port" in res_csv.data

        # Export JSON
        res_json = client.get(f"/api/decks/{d.id}/export?format=json")
        assert res_json.status_code == 200
        assert res_json.get_json()["cards_count"] >= 2

        # Export Anki
        res_anki = client.get(f"/api/decks/{d.id}/export?format=anki")
        assert res_anki.status_code == 200
        assert b"#deck:" in res_anki.data

        # Export PDF Printable
        res_pdf = client.get(f"/api/decks/{d.id}/export?format=pdf")
        assert res_pdf.status_code == 200
        assert res_pdf.data.startswith(b"%PDF-1.4")


def test_deck_import_files(client, app):
    """Kiểm thử nhập bộ thẻ thông qua tải file đa định dạng: CSV, BOM-CSV, Anki TXT, Excel (.xlsx)."""
    import io

    with app.app_context():
        u, d = setup_deck_and_user()

        # 1. Nhập file CSV có BOM (UTF-8-SIG từ Windows Excel)
        bom_csv_data = "\ufeffQuestion,Answer,Personal Notes\nDog,Con chó,Động vật 4 chân\nCat,Con mèo,Bắt chuột\n".encode(
            "utf-8-sig"
        )
        res_csv = client.post(
            f"/api/decks/{d.id}/import",
            data={"file": (io.BytesIO(bom_csv_data), "vocab.csv")},
            content_type="multipart/form-data",
        )
        assert res_csv.status_code == 201
        assert res_csv.get_json()["created_count"] == 2

        # 2. Nhập file TXT Anki có metadata comment (#separator:tab, #deck:)
        anki_txt_data = (
            "#separator:tab\n"
            "#html:true\n"
            "#deck:English\n"
            "Front\tBack\tPersonal Notes\n"
            "Sun\tMặt trời\tNgôi sao trung tâm\n"
            "Moon\tMặt trăng\tVệ tinh Trái Đất\n"
        ).encode("utf-8")
        res_anki = client.post(
            f"/api/decks/{d.id}/import",
            data={"file": (io.BytesIO(anki_txt_data), "anki_deck.txt")},
            content_type="multipart/form-data",
        )
        assert res_anki.status_code == 201
        assert res_anki.get_json()["created_count"] == 2

        # 3. Nhập file Excel (.xlsx) chuẩn openpyxl
        try:
            import openpyxl  # type: ignore

            wb = openpyxl.Workbook()
            ws = wb.active
            if ws is not None:
                ws.append(["Question", "Answer", "Personal Notes"])
                ws.append(["Computer", "Máy vi tính", "Thiết bị điện tử"])
                ws.append(["Keyboard", "Bàn phím", "Thiết bị nhập liệu"])
            excel_buf = io.BytesIO()
            wb.save(excel_buf)
            excel_bytes = excel_buf.getvalue()

            res_xlsx = client.post(
                f"/api/decks/{d.id}/import",
                data={"file": (io.BytesIO(excel_bytes), "test_vocab.xlsx")},
                content_type="multipart/form-data",
            )
            assert res_xlsx.status_code == 201
            assert res_xlsx.get_json()["created_count"] == 2
        except ImportError:
            pass
