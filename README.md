# EduFlash AI — Intelligent Offline Flashcard System

> Trợ lý học tập thông minh chuyển đổi tài liệu đa phương tiện (PDF, Audio bài giảng, Raw Text) thành Flashcard tương tác, vận hành hoàn toàn offline với mô hình ngôn ngữ lớn (LLM) và thuật toán lặp lại ngắt quãng SM-2 (SuperMemo-2).

---

## 1. Tổng quan Dự án

EduFlash AI là hệ thống mã nguồn mở dạng monorepo phục vụ học tập cá nhân hóa:
- **Trích xuất trọng tâm & Sinh thẻ tự động:** Chuyển đổi nội dung tài liệu học tập thành các cặp câu hỏi - đáp án (Q&A) chuẩn xác bằng LLM cục bộ (không gửi dữ liệu ra bên ngoài qua Internet).
- **Nhận dạng tiếng nói (Speech-to-Text):** Tích hợp Whisper offline để bóc băng trực tiếp file ghi âm bài giảng (.mp3, .wav, .m4a) thành văn bản trước khi sinh flashcard.
- **Tối ưu hóa ghi nhớ với SM-2:** Thuật toán Spaced Repetition tính toán chu kỳ ôn tập tối ưu (Again, Hard, Good, Easy) dựa trên hệ số độ dễ (Easiness Factor) và khoảng cách ngày ôn (Interval).
- **Trải nghiệm học tập hiện đại:** Giao diện thẻ xoay 3D CSS, phát âm giọng nói bản địa (Web Speech TTS) và hệ thống phím tắt tốc độ cao (`Space`, `1`, `2`, `3`, `4`).

---

## 2. Kiến trúc Hệ thống & Cấu trúc Monorepo

Dự án được phân rã thành 3 tầng microservice độc lập kết nối qua giao thức REST HTTP:

```text
EduFlash-AI/
├── client/                     # Frontend SPA (NiceGUI + Tailwind CSS) [Port 5000]
│   ├── assets/                 # Logo, favicon, static assets
│   ├── components/             # Reusable UI widgets (Flashcard 3D, Navbar, Dropzone, Stats)
│   ├── pages/                  # Route views (Home, Study, Decks, Cards, Profile, Auth)
│   ├── services/               # REST API clients & auth guards
│   ├── main.py                 # Client app entrypoint
│   └── requirements.txt        # Client dependencies (nicegui, httpx, python-dotenv)
│
├── server/                     # Backend API & SQLite Gateway [Port 3000]
│   ├── app/
│   │   ├── api/                # Modular REST Blueprints (ai_gateway, cards, study, decks, auth)
│   │   ├── core/               # Database initialization & app configs
│   │   ├── models/             # SQLAlchemy ORM models (13 tables: Deck, Card, StudyReview, ...)
│   │   ├── services/           # SM-2 engine, AI gateway bridge, deck import/export
│   │   └── main.py             # Flask application entrypoint & Swagger UI (/docs/)
│   ├── scripts/                # E2E test runner, Node dev orchestrator (dev.js)
│   ├── schema.sql              # 3NF SQLite database relational schema DDL
│   ├── tests/                  # Pytest automated test suites (24 unit & integration tests)
│   └── requirements.txt        # Server dependencies (flask, sqlalchemy, flasgger, pypdf)
│
├── pipeline/                   # Offline AI Inference Engine [Port 8000]
│   ├── app/
│   │   └── main.py             # FastAPI async inference service & OpenAPI docs (/docs)
│   ├── models_weights/         # Local model weights directory (Qwen2.5-0.5B-Instruct, Whisper)
│   ├── src/
│   │   ├── cleaners/           # Unicode & text sanitization
│   │   ├── processors/         # Card generator, chat templates, multi-tier output parser
│   │   └── download_model.py   # Script download weights từ Hugging Face Hub
│   └── requirements.txt        # Pipeline dependencies (transformers, torch, whisper, fastapi)
│
├── scripts/                    # Cross-platform orchestration & automation
│   ├── setup.js                # Node setup script (initializes .venv & installs pip packages)
│   └── download_model.js       # Node download helper
├── package.json                # npm scripts runner (concurrent execution & dev shortcuts)
├── setup.bat                   # Windows Batch 1-click setup script
├── setup.ps1                   # Windows PowerShell 1-click setup script
├── setup.sh                    # Linux/macOS POSIX Bash 1-click setup script
├── .env.example                # Root environment template
└── .gitignore                  # Git ignore rules
```

---

## 3. Yêu cầu Hệ thống (Prerequisites)

- **Hệ điều hành:** Windows 10/11, macOS 12+, hoặc Linux (Ubuntu 20.04+).
- **Python:** Phiên bản 3.10 trở lên (khuyến nghị Python 3.11 hoặc 3.12/3.13).
- **Node.js:** Phiên bản 18+ (tùy chọn, dùng cho `npm start` và quản lý tiến trình song song).
- **Dung lượng đĩa trống:**
  - Codebase & Virtualenvs: ~1.5 GB.
  - Model weights Qwen2.5-0.5B-Instruct: ~950 MB.
  - Model weights Whisper (base): ~150 MB.
- **Phần cứng:**
  - CPU: 4 cores trở lên.
  - RAM: Tối thiểu 8 GB (khuyến nghị 16 GB).
  - GPU: Không bắt buộc (mô hình tối ưu chạy mượt trên CPU; tự động kích hoạt CUDA nếu có NVIDIA GPU).

---

## 4. Hướng dẫn Cài đặt & Khởi chạy Từng bước (Quick Start)

### Cách 1: Tự động hóa hoàn toàn với npm (Khuyến nghị)

Nếu máy đã cài Node.js, bạn có thể thiết lập và khởi chạy toàn bộ 3 tầng bằng 2 lệnh:

```bash
# 1. Clone repository
git clone https://github.com/your-username/EduFlash-AI.git
cd EduFlash-AI

# 2. Cài đặt tự động môi trường (tạo .venv và pip install cho cả 3 modules)
npm install

# 3. Tải weights mô hình AI offline về máy (~950MB)
npm run download-model

# 4. Khởi chạy song song cả 3 dịch vụ (Backend, Pipeline, Client)
npm start
```

### Cách 2: Sử dụng Script 1-Click (Không cần Node.js)

Dành cho môi trường chỉ có Python thuần:

**Trên Windows (PowerShell):**
```powershell
.\setup.ps1
.\pipeline\.venv\Scripts\python.exe pipeline\src\download_model.py
python server\scripts\run_e2e_stack.py
```

**Trên Windows (Command Prompt):**
```cmd
setup.bat
pipeline\.venv\Scripts\python.exe pipeline\src\download_model.py
python server\scripts\run_e2e_stack.py
```

**Trên Linux / macOS (Bash):**
```bash
chmod +x setup.sh
./setup.sh
pipeline/.venv/bin/python pipeline/src/download_model.py
python3 server/scripts/run_e2e_stack.py
```

### Cách 3: Cài đặt và khởi chạy thủ công từng module

Nếu muốn debug hoặc chạy độc lập từng terminal riêng:

#### Terminal 1: Backend Server (Port 3000)
```bash
cd server
python -m venv .venv
# Kích hoạt venv (Windows: .venv\Scripts\activate | Unix: source .venv/bin/activate)
pip install -r requirements.txt
python app/main.py
```

#### Terminal 2: AI Pipeline Microservice (Port 8000)
```bash
cd pipeline
python -m venv .venv
# Kích hoạt venv
pip install -r requirements.txt
python src/download_model.py
python -m app.main
```

#### Terminal 3: Frontend Client (Port 5000)
```bash
cd client
python -m venv .venv
# Kích hoạt venv
pip install -r requirements.txt
python main.py
```

---

## 5. Hướng dẫn Tải Model AI Offline

Hệ thống hoạt động offline hoàn toàn nhờ mô hình mã nguồn mở gọn nhẹ `Qwen2.5-0.5B-Instruct` và Whisper.

Để tải model offline về thư mục `pipeline/models_weights/`:
```bash
# Qua npm script:
npm run download-model

# Hoặc qua lệnh Python trực tiếp:
cd pipeline
python src/download_model.py
```

Weights sẽ được lưu trữ cấu trúc:
```text
pipeline/models_weights/qwen2.5-0.5b/
├── config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
└── vocab.json
```

---

## 6. Luồng Trải nghiệm Người dùng (User Flow Walkthrough)

Truy cập ứng dụng tại trình duyệt: `http://localhost:5000`

### Bước 1: Tạo thẻ tại Studio (`/`)
1. Nhập đoạn văn bản bài học hoặc kéo thả tài liệu giáo trình (`.pdf`, `.txt`, `.docx`) hoặc file ghi âm (`.mp3`, `.wav`, `.m4a`).
2. Chọn độ khó và số lượng thẻ dự kiến (mặc định 3-5 thẻ/phân đoạn).
3. Nhấp nút **⚡ Sinh Flashcard Tự Động**. Nếu nạp file audio, Whisper AI sẽ bóc băng phụ đề trước khi chuyển sang LLM trích xuất Q&A.

### Bước 2: Duyệt, Tùy chỉnh & Lưu vào Bộ thẻ
1. AI trả về danh sách thẻ nháp hiển thị trực quan dưới dạng thẻ tương tác.
2. Bạn có thể chỉnh sửa trực tiếp câu hỏi, đáp án, giải thích, gán Tag hoặc thêm gợi ý mẹo nhớ.
3. Chọn Deck đích (hoặc tạo Deck mới) và nhấp **Lưu vào Bộ Thẻ** (`POST /api/cards/batch`).

### Bước 3: Ôn tập ngắt quãng với Thuật toán SM-2 (`/study`)
1. Truy cập trang **Ôn tập**, chọn Bộ thẻ cần học từ danh sách Deck Picker.
2. Thẻ flashcard 3D hiển thị mặt trước:
   - Nhấn **Space** hoặc nhấp vào thẻ để kích hoạt hiệu ứng xoay 180 độ xem đáp án.
   - Nhấp biểu tượng loa 🔊 để nghe phát âm bản xứ (Web Speech API TTS, xử lý độc lập không gây kích hoạt lật thẻ).
   - Nhấp biểu tượng bút để thêm ghi chú/mẹo nhớ cá nhân.
3. Đánh giá mức độ nhớ theo chuẩn thang đo SM-2:
   - Phím **1** / Nút đỏ: **Quên (Again)** — Lặp lại ngay sau 1 phút.
   - Phím **2** / Nút cam: **Khó (Hard)** — Giảm hệ số Ease Factor.
   - Phím **3** / Nút xanh lam: **Tốt (Good)** — Tăng interval chuẩn.
   - Phím **4** / Nút xanh lá: **Dễ (Easy)** — Tăng vọt interval cho chu kỳ tiếp theo.
4. Khi hoàn thành toàn bộ thẻ, màn hình **Chúc mừng (Study Congrats)** tổng kết số thẻ đã học, tỉ lệ chính xác và thời gian tập trung.

---

## 7. Bảng Quy chuẩn Biến Môi trường (.env Config)

### Root (`.env`)
```ini
PORT=3000
PIPELINE_PORT=8000
CLIENT_PORT=5000

BACKEND_API_URL=http://127.0.0.1:3000/api
AI_PIPELINE_URL=http://127.0.0.1:8000/api
CLIENT_ORIGIN=http://127.0.0.1:5000
```

### Backend Server (`server/.env`)
```ini
PORT=3000
HOST=0.0.0.0
SECRET_KEY=dev-secret-key-3000
DATABASE_URL=sqlite:///instance/database.db
AI_PIPELINE_URL=http://127.0.0.1:8000/api
CLIENT_ORIGIN=http://127.0.0.1:5000
```

### AI Pipeline (`pipeline/.env`)
```ini
PORT=8000
HOST=0.0.0.0
MODEL_PATH=models_weights/qwen2.5-0.5b
WHISPER_MODEL_SIZE=base
DEVICE=cpu
```
*(Nếu máy có card đồ họa NVIDIA CUDA, đổi `DEVICE=cuda` để tăng tốc độ suy luận gấp 5-10 lần).*

### Client (`client/.env`)
```ini
PORT=5000
HOST=0.0.0.0
BACKEND_API_URL=http://127.0.0.1:3000/api
```

---

## 8. Kiểm thử & Đảm bảo Chất lượng (Testing)

Chạy bộ kiểm thử tự động toàn diện:
```bash
# Kiểm thử 24 test case của Backend CRUD & Gateway (100% Pass)
python -m pytest server/tests -v

# Kiểm thử bộ tách chuỗi đầu ra Qwen / T5 Parser
python pipeline/test_parser.py

# Kiểm thử toàn bộ 7 trang giao diện NiceGUI Client
python client/test_pages.py

# Kiểm thử các thành phần UI, 3D Flashcard & Dropzone RAM
python client/test_components.py
```
