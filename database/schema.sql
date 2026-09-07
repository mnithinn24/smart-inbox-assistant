-- ============================================================
-- Smart Inbox Assistant — MySQL Database Schema
-- ============================================================
-- All data is synthetic / fictional — no real patient data.
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_inbox
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smart_inbox;

-- ============================================================
-- TABLE 1: inbox_messages — Every email received
-- ============================================================
CREATE TABLE IF NOT EXISTS inbox_messages (
    message_id        INT AUTO_INCREMENT PRIMARY KEY,
    email_uid         VARCHAR(255) UNIQUE,
    sender            VARCHAR(500),
    subject           VARCHAR(1000),
    received_date     DATETIME,
    body_text         LONGTEXT,
    body_html         LONGTEXT,
    fetch_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status ENUM('PENDING','PROCESSING','COMPLETED','ERROR')
                      DEFAULT 'PENDING',
    error_message     TEXT,
    processing_time_ms INT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_status (processing_status),
    INDEX idx_received (received_date)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 2: attachments — Files attached to emails
-- ============================================================
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id      INT AUTO_INCREMENT PRIMARY KEY,
    message_id         INT NOT NULL,
    filename           VARCHAR(500),
    content_type       VARCHAR(255),
    file_size          INT,
    file_path          VARCHAR(1000),
    pdf_type           ENUM('DIGITAL','SCANNED','ARTICLE','NON_ENGLISH') NULL,
    detected_language  VARCHAR(50),
    ocr_confidence     DECIMAL(5,2),
    extracted_text     LONGTEXT,
    translated_text    LONGTEXT,
    original_text      LONGTEXT,
    ai_summary         TEXT,
    table_data         JSON,
    image_descriptions JSON,
    processing_time_ms INT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES inbox_messages(message_id) ON DELETE CASCADE,
    INDEX idx_msg (message_id),
    INDEX idx_pdf_type (pdf_type)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 3: classifications — AI sorting results
-- ============================================================
CREATE TABLE IF NOT EXISTS classifications (
    classification_id  INT AUTO_INCREMENT PRIMARY KEY,
    message_id         INT NOT NULL,
    category           ENUM('ICSR','PQC','MI','NOT_RELEVANT'),
    confidence_score   DECIMAL(5,2),
    ai_reason          VARCHAR(2000),
    reviewer_action    ENUM('PENDING','ACCEPTED','OVERRIDDEN') DEFAULT 'PENDING',
    reviewer_override  VARCHAR(50),
    reviewer_notes     TEXT,
    reviewed_by        VARCHAR(255),
    reviewed_at        TIMESTAMP NULL,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES inbox_messages(message_id) ON DELETE CASCADE,
    INDEX idx_msg (message_id),
    INDEX idx_cat (category),
    INDEX idx_review (reviewer_action)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 4: icsr_extractions — Safety Report facts
-- ============================================================
CREATE TABLE IF NOT EXISTS icsr_extractions (
    extraction_id       INT AUTO_INCREMENT PRIMARY KEY,
    message_id          INT NOT NULL,
    patient_age         VARCHAR(100) DEFAULT 'Not stated',
    patient_sex         VARCHAR(50)  DEFAULT 'Not stated',
    patient_weight      VARCHAR(100) DEFAULT 'Not stated',
    patient_height      VARCHAR(100) DEFAULT 'Not stated',
    patient_history     TEXT,
    reporter_name       VARCHAR(500) DEFAULT 'Not stated',
    reporter_role       VARCHAR(255) DEFAULT 'Not stated',
    reporter_country    VARCHAR(100) DEFAULT 'Not stated',
    product_name        VARCHAR(500) DEFAULT 'Not stated',
    product_dose        VARCHAR(255) DEFAULT 'Not stated',
    product_route       VARCHAR(255) DEFAULT 'Not stated',
    product_start_date  VARCHAR(100) DEFAULT 'Not stated',
    product_stop_date   VARCHAR(100) DEFAULT 'Not stated',
    reaction_description TEXT,
    reaction_onset_date  VARCHAR(100) DEFAULT 'Not stated',
    reaction_outcome     VARCHAR(255) DEFAULT 'Not stated',
    is_serious          ENUM('Yes','No','Unknown') DEFAULT 'Unknown',
    seriousness_criteria VARCHAR(500),
    ai_narrative        TEXT,
    field_confidence    JSON,
    source_references   JSON,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES inbox_messages(message_id) ON DELETE CASCADE,
    INDEX idx_msg (message_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 5: pqc_extractions — Quality Complaint facts
-- ============================================================
CREATE TABLE IF NOT EXISTS pqc_extractions (
    extraction_id          INT AUTO_INCREMENT PRIMARY KEY,
    message_id             INT NOT NULL,
    product_name           VARCHAR(500) DEFAULT 'Not stated',
    batch_lot_number       VARCHAR(255) DEFAULT 'Not stated',
    complaint_description  TEXT,
    photo_mentioned        ENUM('Yes','No','Unknown') DEFAULT 'Unknown',
    source_references      JSON,
    field_confidence       JSON,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES inbox_messages(message_id) ON DELETE CASCADE,
    INDEX idx_msg (message_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 6: mi_extractions — Medical Info Request facts
-- ============================================================
CREATE TABLE IF NOT EXISTS mi_extractions (
    extraction_id     INT AUTO_INCREMENT PRIMARY KEY,
    message_id        INT NOT NULL,
    questions_asked   JSON,
    product_topic     VARCHAR(500) DEFAULT 'Not stated',
    source_references JSON,
    field_confidence  JSON,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES inbox_messages(message_id) ON DELETE CASCADE,
    INDEX idx_msg (message_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 7: audit_log — Every AI decision + reviewer action
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    log_id            INT AUTO_INCREMENT PRIMARY KEY,
    message_id        INT,
    action_type       VARCHAR(100) NOT NULL,
    action_detail     JSON,
    performed_by      VARCHAR(255),
    input_snapshot    LONGTEXT,
    output_snapshot   LONGTEXT,
    timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES inbox_messages(message_id) ON DELETE SET NULL,
    INDEX idx_msg (message_id),
    INDEX idx_action (action_type),
    INDEX idx_time (timestamp)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 8: literature_articles (Bonus)
-- ============================================================
CREATE TABLE IF NOT EXISTS literature_articles (
    article_id         INT AUTO_INCREMENT PRIMARY KEY,
    filename           VARCHAR(500),
    file_path          VARCHAR(1000),
    extracted_text     LONGTEXT,
    upload_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status  ENUM('PENDING','PROCESSING','COMPLETED','ERROR') DEFAULT 'PENDING',
    processing_time_ms INT
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 9: literature_cases (Bonus)
-- ============================================================
CREATE TABLE IF NOT EXISTS literature_cases (
    case_id              INT AUTO_INCREMENT PRIMARY KEY,
    article_id           INT NOT NULL,
    case_number          INT,
    is_reportable        ENUM('Yes','No') DEFAULT 'No',
    relevance_reason     TEXT,
    case_summary         TEXT,
    patient_identifiable ENUM('Yes','No') DEFAULT 'No',
    confidence_score     DECIMAL(5,2),
    source_location      VARCHAR(500),
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (article_id) REFERENCES literature_articles(article_id) ON DELETE CASCADE,
    INDEX idx_article (article_id)
) ENGINE=InnoDB;
