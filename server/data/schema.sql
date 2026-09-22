PRAGMA page_size = 16384;
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 1. Bảng Roles (Giữ nguyên INTEGER autoincrement: 1=admin, 2=user)
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL UNIQUE,
    description TEXT
);

INSERT OR IGNORE INTO roles (id, name, description) VALUES
(1, 'admin', 'Quản trị viên: thẩm định, chỉnh sửa và đánh giá độ chính xác'),
(2, 'user', 'Người dùng: sử dụng camera OCR thời gian thực');

-- 2. Bảng Users (UUID v4 Primary Key & Password Hash)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    google_id VARCHAR(100) UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(100),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    role_id INTEGER NOT NULL DEFAULT 2,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

INSERT OR IGNORE INTO users (id, google_id, email, password_hash, full_name, role_id, is_active) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'admin_default', 'admin@system.local', 'scrypt:32768:8:1$lQ17xvm4CDWZJ6Jw$056dc4a87c17561c0bfeb839f395fe22c5f807cadd9fcbdbb37b244f9f559b55525df4db9a65e631527698c3ad14b0f12ac34c18e2b86d5ccd2616515e34b103', 'Default Admin', 1, 1),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', 'customer_default', 'customer@shop.vn', 'scrypt:32768:8:1$wAs2UGIyT9u1cMBM$f273f769b6057be5cd35bf3d38e8c6a73a5253a47bfc120fe64365303e26e9b2692fc989e08dff9ce1b5d5bb213f176ac01453668ef946851638666ccdb45f76', 'Khách Hàng Mẫu', 2, 1),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbc', 'user_default', 'user@system.local', 'scrypt:32768:8:1$N9bCwNA6inWkM9f5$954ac9c2f5ecf8a799e8d57fb641c9a52d7e37a27252930ab27484e526b2fe2323de18100df89e3814dfc2b864ee09442c83617cd175e14cc00d50d425dc1fdb', 'Người Dùng Test', 2, 1);

-- 3. Bảng OCR Records (UUID v4 & SQLite BLOB)
CREATE TABLE IF NOT EXISTS ocr_records (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Ảnh chụp gốc từ Camera
    raw_image_data BLOB NOT NULL,
    raw_image_mime VARCHAR(30) DEFAULT 'image/jpeg' NOT NULL,
    
    -- Ảnh sau khi AI vẽ Bounding Box
    annotated_image_data BLOB,
    annotated_image_mime VARCHAR(30) DEFAULT 'image/jpeg',
    
    raw_detected_text TEXT NOT NULL,
    ocr_json_data TEXT NOT NULL,
    
    -- Dữ liệu Audio MP3 nhị phân
    audio_data BLOB NOT NULL,
    audio_mime VARCHAR(30) DEFAULT 'audio/mpeg' NOT NULL,
    
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ocr_records_user_id ON ocr_records (user_id);
CREATE INDEX IF NOT EXISTS idx_ocr_records_created_at ON ocr_records (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_records_user_status_id ON ocr_records (user_id, status, id DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_records_status_id ON ocr_records (status, id DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_records_user_status_created ON ocr_records (user_id, status, created_at DESC);

-- 4. Bảng OCR Reviews (UUID v4 & SQLite Audio BLOB)
CREATE TABLE IF NOT EXISTS ocr_reviews (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    record_id VARCHAR(36) NOT NULL UNIQUE,
    admin_id VARCHAR(36) NOT NULL,
    corrected_text TEXT NOT NULL,
    
    -- File audio phát âm lại sau khi Admin sửa nội dung
    corrected_audio_data BLOB NOT NULL,
    corrected_audio_mime VARCHAR(30) DEFAULT 'audio/mpeg' NOT NULL,
    
    accuracy_score REAL NOT NULL,
    review_notes TEXT,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (record_id) REFERENCES ocr_records (id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_ocr_reviews_record_id ON ocr_reviews (record_id);
CREATE INDEX IF NOT EXISTS idx_ocr_reviews_admin_id ON ocr_reviews (admin_id, id DESC);

-- =======================================================
-- MỞ RỘNG TÍNH NĂNG E-COMMERCE (UUID v4)
-- =======================================================

-- 5. Bảng Danh mục sản phẩm (Categories - UUID v4)
CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- 6. Bảng Sản phẩm (Products - UUID v4)
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    category_id VARCHAR(36),
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

-- 7. Bảng Giỏ hàng (Cart Items - UUID v4)
CREATE TABLE IF NOT EXISTS cart_items (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    record_id VARCHAR(36),
    quantity INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES ocr_records (id) ON DELETE SET NULL,
    UNIQUE(user_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items (user_id);

-- 8. Bảng Đơn hàng (Orders - UUID v4)
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    user_id VARCHAR(36) NOT NULL,
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

-- 9. Bảng Chi tiết đơn hàng (Order Items - UUID v4)
CREATE TABLE IF NOT EXISTS order_items (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);