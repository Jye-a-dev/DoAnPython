PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 1. Bảng Roles
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL UNIQUE,
    description TEXT
);

INSERT OR IGNORE INTO roles (id, name, description) VALUES
(1, 'admin', 'Quản trị viên: thẩm định, chỉnh sửa và đánh giá độ chính xác'),
(2, 'user', 'Người dùng: sử dụng camera OCR thời gian thực');

-- 2. Bảng Users (Google Login)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id VARCHAR(100) UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    role_id INTEGER NOT NULL DEFAULT 2,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- 3. Bảng OCR Records (Lưu Text gốc + Audio gốc từ Camera/Frame)
CREATE TABLE IF NOT EXISTS ocr_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    image_url TEXT NOT NULL,
    raw_detected_text TEXT NOT NULL,
    ocr_json_data TEXT NOT NULL,
    audio_url TEXT NOT NULL,                  -- File MP3 đọc text nhận diện tự động
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ocr_records_user_id ON ocr_records (user_id);
CREATE INDEX IF NOT EXISTS idx_ocr_records_created_at ON ocr_records (created_at DESC);

-- 4. Bảng Reviews (Lưu Text đã sửa + Audio chuẩn sau khi sửa)
CREATE TABLE IF NOT EXISTS ocr_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL UNIQUE,
    admin_id INTEGER NOT NULL,
    corrected_text TEXT NOT NULL,              -- Text chuẩn sau khi Admin sửa
    corrected_audio_url TEXT NOT NULL,        -- File MP3 mới đọc lại đoạn text chuẩn
    accuracy_score REAL NOT NULL,              -- Độ chính xác (0.0 -> 1.0)
    review_notes TEXT,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (record_id) REFERENCES ocr_records (id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_ocr_reviews_record_id ON ocr_reviews (record_id);