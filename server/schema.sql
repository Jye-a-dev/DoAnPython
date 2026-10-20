-- ============================================================================
-- Flashcard AI Pipeline - 3NF Relational Database Schema (SQLite)
-- Spaced Repetition (SM-2) & Binary Document Storage (BLOB)
-- ============================================================================
PRAGMA foreign_keys = ON;

-- 1. USERS TABLE
CREATE TABLE
    IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(80) NOT NULL UNIQUE,
        email VARCHAR(120) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- 2. USER PROFILES TABLE (1:1 with users)
CREATE TABLE
    IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        full_name VARCHAR(120),
        avatar_url VARCHAR(255),
        bio TEXT,
        timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles (user_id);

-- 3. CATEGORIES TABLE
CREATE TABLE
    IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        color_code VARCHAR(7) DEFAULT '#3B82F6',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_categories_user_id ON categories (user_id);

-- 4. FOLDERS TABLE (Hierarchical structure)
CREATE TABLE
    IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER,
        parent_id INTEGER,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL,
        FOREIGN KEY (parent_id) REFERENCES folders (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_folders_user_id ON folders (user_id);

CREATE INDEX IF NOT EXISTS idx_folders_category_id ON folders (category_id);

CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders (parent_id);

-- 5. DECKS TABLE
CREATE TABLE
    IF NOT EXISTS decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        folder_id INTEGER,
        category_id INTEGER,
        title VARCHAR(150) NOT NULL,
        description TEXT,
        is_public BOOLEAN NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE SET NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
    );

CREATE INDEX IF NOT EXISTS idx_decks_user_id ON decks (user_id);

CREATE INDEX IF NOT EXISTS idx_decks_folder_id ON decks (folder_id);

CREATE INDEX IF NOT EXISTS idx_decks_category_id ON decks (category_id);

-- 6. DOCUMENTS TABLE (Direct In-Memory BLOB Storage)
CREATE TABLE
    IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename VARCHAR(255) NOT NULL,
        file_type VARCHAR(50) NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        file_blob BLOB NOT NULL,
        extracted_text TEXT,
        content_hash VARCHAR(64) NOT NULL UNIQUE,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents (user_id);

CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents (content_hash);

-- 7. CARDS TABLE
CREATE TABLE
    IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER,
        document_id INTEGER,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        explanation TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE,
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE SET NULL
    );

CREATE INDEX IF NOT EXISTS idx_cards_deck_id ON cards (deck_id);

CREATE INDEX IF NOT EXISTS idx_cards_document_id ON cards (document_id);

-- 8. TAGS TABLE
CREATE TABLE
    IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name VARCHAR(50) NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags (user_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_tags_user_name ON tags (user_id, name);

-- 9. CARD_TAGS TABLE (Junction Table M:N)
CREATE TABLE
    IF NOT EXISTS card_tags (
        card_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (card_id, tag_id),
        FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_card_tags_card_id ON card_tags (card_id);

CREATE INDEX IF NOT EXISTS idx_card_tags_tag_id ON card_tags (tag_id);

-- 10. STUDY_SESSIONS TABLE
CREATE TABLE
    IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        deck_id INTEGER NOT NULL,
        start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        total_cards_reviewed INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON study_sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_study_sessions_deck_id ON study_sessions (deck_id);

-- 11. STUDY_REVIEWS TABLE (Spaced Repetition SM-2 Implementation)
CREATE TABLE
    IF NOT EXISTS study_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        card_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        ease_factor REAL NOT NULL DEFAULT 2.5,
        interval_days INTEGER NOT NULL DEFAULT 1,
        repetitions INTEGER NOT NULL DEFAULT 0,
        next_review_date DATETIME,
        reviewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES study_sessions (id) ON DELETE CASCADE,
        FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_study_reviews_session_id ON study_reviews (session_id);

CREATE INDEX IF NOT EXISTS idx_study_reviews_card_id ON study_reviews (card_id);

CREATE INDEX IF NOT EXISTS idx_study_reviews_user_id ON study_reviews (user_id);

CREATE INDEX IF NOT EXISTS idx_study_reviews_next_date ON study_reviews (next_review_date);

-- 12. USER_FAVORITES TABLE
CREATE TABLE
    IF NOT EXISTS user_favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        deck_id INTEGER,
        card_id INTEGER,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE,
        FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites (user_id);

CREATE INDEX IF NOT EXISTS idx_user_favorites_deck_id ON user_favorites (deck_id);

CREATE INDEX IF NOT EXISTS idx_user_favorites_card_id ON user_favorites (card_id);

-- 13. AI_GENERATION_LOGS TABLE
CREATE TABLE
    IF NOT EXISTS ai_generation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        document_id INTEGER,
        deck_id INTEGER,
        prompt_tokens INTEGER NOT NULL DEFAULT 0,
        completion_tokens INTEGER NOT NULL DEFAULT 0,
        model_name VARCHAR(100) NOT NULL DEFAULT 'flan-t5-base',
        status VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
        error_message TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE SET NULL,
        FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE SET NULL
    );

CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_user_id ON ai_generation_logs (user_id);

CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_document_id ON ai_generation_logs (document_id);

CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_deck_id ON ai_generation_logs (deck_id);