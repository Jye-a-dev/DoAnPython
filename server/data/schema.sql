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

INSERT OR IGNORE INTO users (id, google_id, email, full_name, role_id, is_active) VALUES
(1, 'system_default', 'user@system.local', 'Default User', 2, 1);

-- 3. Bảng OCR Records (Lưu Text gốc + Audio gốc từ Camera/Frame)
CREATE TABLE IF NOT EXISTS ocr_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    image_url TEXT NOT NULL,
    raw_detected_text TEXT NOT NULL,
    ocr_json_data TEXT NOT NULL,
    audio_url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ocr_records_user_id ON ocr_records (user_id);
CREATE INDEX IF NOT EXISTS idx_ocr_records_created_at ON ocr_records (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_records_user_status_id ON ocr_records (user_id, status, id DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_records_status_id ON ocr_records (status, id DESC);

-- 4. Bảng Reviews (Lưu Text đã sửa + Audio chuẩn sau khi sửa)
CREATE TABLE IF NOT EXISTS ocr_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL UNIQUE,
    admin_id INTEGER NOT NULL,
    corrected_text TEXT NOT NULL,
    corrected_audio_url TEXT NOT NULL,
    accuracy_score REAL NOT NULL,
    review_notes TEXT,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (record_id) REFERENCES ocr_records (id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_ocr_reviews_record_id ON ocr_reviews (record_id);
CREATE INDEX IF NOT EXISTS idx_ocr_reviews_admin_id ON ocr_reviews (admin_id, id DESC);

-- =======================================================
-- MỞ RỘNG TÍNH NĂNG E-COMMERCE LIÊN KẾT VỚI HỆ THỐNG HIỆN CÓ
-- =======================================================

-- 5. Bảng Danh mục sản phẩm (Categories)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

INSERT OR IGNORE INTO categories (id, name, slug, description) VALUES
(1, 'Thiết bị điện tử', 'thiet-bi-dien-tu', 'Laptop, điện thoại và phụ kiện số'),
(2, 'Đồ uống & Thực phẩm', 'do-uong-thuc-pham', 'Nước uống, đồ ăn nhanh và hoa quả');

-- 6. Bảng Sản phẩm (Products)
-- class_name: Khớp trực tiếp với label nhận diện từ YOLO / OCR (chữ thường, vd: 'laptop', 'bottle', 'apple'...)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    name VARCHAR(150) NOT NULL,
    class_name VARCHAR(50),
    sku VARCHAR(50) UNIQUE,
    price REAL NOT NULL,
    stock_quantity INTEGER DEFAULT 0 NOT NULL,
    image_url TEXT,
    description TEXT,
    is_available BOOLEAN DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_products_class_name ON products (class_name);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku);

INSERT OR IGNORE INTO products (id, category_id, name, class_name, sku, price, stock_quantity, image_url, description, is_available) VALUES
(1, 1, 'Laptop Dell Inspiron 15', 'laptop', 'LAP-DELL-15', 18500000.0, 15, '/static/uploads/dell_15.jpg', 'Laptop văn phòng cấu hình cao', 1),
(2, 2, 'Chai nước khoáng Lavie 500ml', 'bottle', 'BOT-LAV-500', 10000.0, 100, '/static/uploads/lavie_500.jpg', 'Nước khoáng thiên nhiên đóng chai', 1),
(3, 2, 'Táo Envy New Zealand', 'apple', 'FRUIT-APP-01', 35000.0, 50, '/static/uploads/apple_envy.jpg', 'Táo giòn ngọt nhập khẩu', 1);

-- 7. Bảng Giỏ hàng (Cart Items)
-- record_id: INTEGER NULL đáp ứng quy tắc ON DELETE SET NULL khi bản ghi quét camera bị xóa
CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    record_id INTEGER,
    quantity INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES ocr_records (id) ON DELETE SET NULL,
    UNIQUE(user_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items (user_id);

-- 8. Bảng Đơn hàng (Orders)
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    shipping_address TEXT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    status VARCHAR(30) DEFAULT 'pending' NOT NULL,
    audio_confirmation_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);

-- 9. Bảng Chi tiết đơn hàng (Order Items)
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);