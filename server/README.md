# Smart Object Detector (Reflex + FastAPI + YOLO + SQLite)

Hệ thống thị giác máy tính nhận diện đối tượng theo kiến trúc chuẩn 3 tầng độc lập:
- `pipeline/`: Đóng gói toàn bộ AI Inference (YOLOv8/YOLO11), xử lý ảnh và tổng hợp giọng nói (edge-tts / gTTS).
- `server/`: Backend FastAPI Gateway, Static Media Serving, kết nối SQLite qua SQLModel.
- `client/`: Bảng điều khiển giao diện người dùng viết bằng Reflex (Python thuần).

---

## 1. Cấu trúc dự án chuẩn hóa

```text
smart_object_detector/
├── pipeline/                   # Toàn bộ AI inference & Xử lý media
│   ├── __init__.py
│   ├── schemas.py              # Pydantic models (ObjectItem, BoundingBox, DetectionResult)
│   ├── detector.py             # YOLO (ultralytics, vẽ box, mapping tiếng Việt, summary)
│   └── tts_engine.py           # Text-to-Speech (edge-tts fallback sang gTTS)
├── server/                     # Toàn bộ API Backend, Database & Static Serving
│   ├── static/
│   │   ├── uploads/            # Lưu trữ ảnh raw và ảnh annotated
│   │   └── audio/              # Lưu trữ các file mp3 sinh ra
│   ├── database.py             # SQLite config (SQLModel/SQLite engine, DetectionRecord model)
│   ├── app.py                  # FastAPI app (CORS, mounts static, /detect, /history)
│   └── requirements.txt
├── client/                     # Toàn bộ giao diện tương tác Frontend
│   ├── rxconfig.py             # Cấu hình Reflex
│   ├── state.py                # Reflex State (upload, async httpx call sang server, audio state)
│   ├── app.py                  # Reflex UI Dashboard (upload, audio player, JSON viewer, history)
│   └── requirements.txt
├── data/                       # Chứa file SQLite detections.db
└── README.md
```

---

## 2. Cài đặt môi trường

### Khởi tạo môi trường ảo Python
```bash
python -m venv venv

# Kích hoạt trên Windows:
.\venv\Scripts\activate

# Kích hoạt trên Linux/macOS:
source venv/bin/activate
```

### Cài đặt dependencies cho Server & Pipeline
```bash
pip install -r server/requirements.txt
```

### Cài đặt dependencies cho Client
```bash
pip install -r client/requirements.txt
```

---

## 3. Khởi chạy 3 tầng dịch vụ bằng npm
## 3. Khởi chạy các dịch vụ qua npm

Dự án phân tách 3 dịch vụ độc lập quản lý qua tệp `.env`:
Dự án phân tách 3 dịch vụ độc lập với `.env` riêng biệt đặt trong từng thư mục:
- **Client (Reflex Web UI)**: Cổng `5000` (http://localhost:5000)
- **Server (FastAPI Gateway & DB)**: Cổng `3000` (Swagger: http://localhost:3000/docs)
- **Pipeline (YOLO AI & TTS)**: Cổng `3100` (Swagger: http://localhost:3100/docs)
- **Server Gateway**: Cổng `3000` (Swagger: http://localhost:3000/docs)
- **Pipeline AI Inference**: Cổng `3100` (Swagger: http://localhost:3100/docs)

### Cách 1: Khởi chạy từ thư mục gốc dự án
```bash
# Terminal 1: Pipeline AI Inference Service (Port 3100)
npm run pipeline
### Lệnh khởi chạy:

# Terminal 2: Server API Gateway & Database (Port 3000)
npm run server

# Terminal 3: Client Frontend Dashboard (Port 5000)
npm run client
```

### Cách 2: Khởi chạy độc lập trong từng thư mục module
```bash
# Khởi chạy Pipeline Service (Port 3100)
cd pipeline && npm run dev

# Khởi chạy Server Gateway (Port 3000)
# Terminal 1: Chạy Backend (Tự động khởi chạy song song cả Server:3000 và Pipeline:3100)
cd server && npm run dev

# Khởi chạy Client Dashboard (Port 5000)
# Terminal 2: Chạy Frontend Dashboard (Reflex:5000)
cd client && npm run dev
```

> **Lưu ý**: Khi chạy `cd server && npm run dev`, tiến trình `runner.py` sẽ tự động khởi tạo song song cả Pipeline (port 3100) và Server Gateway (port 3000), đồng thời log toàn bộ Port, URL và Swagger Docs lên console.

---

## 4. Đặc tả API Endpoints

### 1. Phân tích đối tượng & Thuyết minh âm thanh
- **Endpoint**: `POST /api/v1/detect`
- **Content-Type**: `multipart/form-data`
- **Tham số**: `image` (tệp hình ảnh JPEG, PNG, WEBP)
- **Cơ chế**: Inference YOLO được điều phối qua `run_in_executor` để giải phóng event loop; sinh giọng đọc thuyết minh tiếng Việt bất đồng bộ; ghi bản ghi vào `data/detections.db`.

### 2. Lịch sử nhận diện
- **Endpoint**: `GET /api/v1/history?limit=10`
- **Phản hồi**: 10 bản ghi nhận diện gần nhất.
