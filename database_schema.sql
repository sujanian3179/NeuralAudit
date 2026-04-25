# NeuralAudit Database Schema
# Create this schema in your Supabase PostgreSQL database

-- Table: audit_results
CREATE TABLE IF NOT EXISTS audit_results (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    product_url TEXT NOT NULL,
    variant_image_url TEXT NOT NULL,
    metadata_color_label TEXT NOT NULL,
    metadata_family TEXT,
    cnn_predicted_class INTEGER,
    predicted_family TEXT,
    cnn_confidence FLOAT,
    heuristic_valid BOOLEAN DEFAULT TRUE,
    heuristic_confidence FLOAT DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('VERIFIED', 'FLAGGED', 'UNCERTAIN')),
    overall_confidence FLOAT,
    UNIQUE(product_url, variant_image_url, metadata_color_label)
);

-- Index for fast queries
CREATE INDEX idx_audit_status ON audit_results(status);
CREATE INDEX idx_audit_product_url ON audit_results(product_url);
CREATE INDEX idx_audit_created_at ON audit_results(created_at);
CREATE INDEX idx_audit_predicted_family ON audit_results(predicted_family);

-- Table: processing_logs
CREATE TABLE IF NOT EXISTS processing_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    product_url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('STARTED', 'COMPLETED', 'FAILED')),
    error_message TEXT,
    variants_count INTEGER,
    processing_time_seconds FLOAT
);

CREATE INDEX idx_logs_product_url ON processing_logs(product_url);
CREATE INDEX idx_logs_status ON processing_logs(status);
CREATE INDEX idx_logs_created_at ON processing_logs(created_at);

-- View: audit_summary
CREATE VIEW IF NOT EXISTS audit_summary AS
SELECT
    product_url,
    COUNT(*) as total_variants,
    SUM(CASE WHEN status = 'VERIFIED' THEN 1 ELSE 0 END) as verified_count,
    SUM(CASE WHEN status = 'FLAGGED' THEN 1 ELSE 0 END) as flagged_count,
    SUM(CASE WHEN status = 'UNCERTAIN' THEN 1 ELSE 0 END) as uncertain_count,
    ROUND(AVG(overall_confidence::NUMERIC), 4) as avg_confidence,
    MAX(created_at) as last_updated
FROM audit_results
GROUP BY product_url;

-- View: daily_statistics
CREATE VIEW IF NOT EXISTS daily_statistics AS
SELECT
    DATE(created_at) as audit_date,
    COUNT(*) as total_audits,
    COUNT(DISTINCT product_url) as unique_products,
    SUM(CASE WHEN status = 'VERIFIED' THEN 1 ELSE 0 END) as verified,
    SUM(CASE WHEN status = 'FLAGGED' THEN 1 ELSE 0 END) as flagged,
    ROUND(SUM(CASE WHEN status = 'VERIFIED' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*), 4) as verification_rate,
    ROUND(AVG(cnn_confidence::NUMERIC), 4) as avg_cnn_confidence
FROM audit_results
GROUP BY DATE(created_at)
ORDER BY audit_date DESC;

-- Row Level Security (optional - configure based on your setup)
-- ALTER TABLE audit_results ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;
