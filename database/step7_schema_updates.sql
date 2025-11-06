-- Step 7: Continuous Improvement Database Schema Updates
-- Add tables for performance monitoring, feedback, and alert management

-- Table for storing model selections
CREATE TABLE IF NOT EXISTS model_selections (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    horizon_hours INTEGER NOT NULL,
    selected_model VARCHAR(100) NOT NULL,
    selection_reason TEXT,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, horizon_hours, created_at)
);

CREATE INDEX idx_model_selections_city_horizon ON model_selections(city, horizon_hours);
CREATE INDEX idx_model_selections_created_at ON model_selections(created_at DESC);

-- Table for user feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'ui_design', 'prediction_accuracy', 'alert_relevance', 
        'alert_timing', 'alert_frequency', 'data_visualization',
        'feature_request', 'bug_report', 'performance', 'other'
    )),
    feedback_text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    page VARCHAR(100),
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'implemented', 'closed')),
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_feedback_category ON user_feedback(category);
CREATE INDEX idx_user_feedback_status ON user_feedback(status);
CREATE INDEX idx_user_feedback_created_at ON user_feedback(created_at DESC);
CREATE INDEX idx_user_feedback_user_id ON user_feedback(user_id);

-- Table for alert rules configuration
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    condition_type VARCHAR(50) NOT NULL CHECK (condition_type IN (
        'aqi_threshold', 'rapid_increase', 'forecast_high', 
        'custom'
    )),
    threshold_value NUMERIC NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    message_template TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alert_rules_city ON alert_rules(city);
CREATE INDEX idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX idx_alert_rules_severity ON alert_rules(severity);

-- Update alerts table to reference rules
ALTER TABLE alerts 
ADD COLUMN IF NOT EXISTS rule_id INTEGER REFERENCES alert_rules(id);

ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS acknowledged BOOLEAN DEFAULT false;

ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP;

ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS acknowledged_by VARCHAR(100);

-- Update predictions table to support performance tracking
ALTER TABLE predictions
ADD COLUMN IF NOT EXISTS actual_aqi NUMERIC;

ALTER TABLE predictions
ADD COLUMN IF NOT EXISTS features JSONB;

ALTER TABLE predictions
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

ALTER TABLE predictions
ADD COLUMN IF NOT EXISTS error NUMERIC GENERATED ALWAYS AS (
    CASE 
        WHEN actual_aqi IS NOT NULL THEN ABS(predicted_aqi - actual_aqi)
        ELSE NULL
    END
) STORED;

-- Indexes for predictions table
CREATE INDEX IF NOT EXISTS idx_predictions_city_horizon ON predictions(city, horizon_hours);
CREATE INDEX IF NOT EXISTS idx_predictions_model_used ON predictions(model_used);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_actual_aqi ON predictions(actual_aqi) WHERE actual_aqi IS NOT NULL;

-- Update model_performance table structure
ALTER TABLE model_performance
ADD COLUMN IF NOT EXISTS mean_error NUMERIC;

ALTER TABLE model_performance
ADD COLUMN IF NOT EXISTS std_error NUMERIC;

ALTER TABLE model_performance
ADD COLUMN IF NOT EXISTS prediction_count INTEGER;

-- Indexes for model_performance
CREATE INDEX IF NOT EXISTS idx_model_performance_city_horizon ON model_performance(city, horizon_hours);
CREATE INDEX IF NOT EXISTS idx_model_performance_timestamp ON model_performance(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_model_performance_model_name ON model_performance(model_name);

-- Table for system configuration and version control
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    description TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

CREATE INDEX idx_system_config_key ON system_config(config_key);

-- Table for change log / audit trail
CREATE TABLE IF NOT EXISTS change_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'delete')),
    changes JSONB,
    user_id VARCHAR(100),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_change_log_entity ON change_log(entity_type, entity_id);
CREATE INDEX idx_change_log_created_at ON change_log(created_at DESC);
CREATE INDEX idx_change_log_user_id ON change_log(user_id);

-- Table for documentation versions
CREATE TABLE IF NOT EXISTS documentation_versions (
    id SERIAL PRIMARY KEY,
    doc_type VARCHAR(50) NOT NULL,
    doc_name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    file_path VARCHAR(500),
    author VARCHAR(100),
    commit_hash VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_type, doc_name, version)
);

CREATE INDEX idx_documentation_versions_type_name ON documentation_versions(doc_type, doc_name);
CREATE INDEX idx_documentation_versions_created_at ON documentation_versions(created_at DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updated_at
DROP TRIGGER IF EXISTS update_user_feedback_updated_at ON user_feedback;
CREATE TRIGGER update_user_feedback_updated_at
    BEFORE UPDATE ON user_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_alert_rules_updated_at ON alert_rules;
CREATE TRIGGER update_alert_rules_updated_at
    BEFORE UPDATE ON alert_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_config_updated_at ON system_config;
CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
    ('performance_monitoring', '{"enabled": true, "update_interval_hours": 1}', 'Performance monitoring configuration'),
    ('auto_model_selection', '{"enabled": true, "selection_interval_hours": 24, "lookback_days": 7}', 'Auto model selection configuration'),
    ('feedback_collection', '{"enabled": true, "min_rating": 1, "max_rating": 5}', 'User feedback collection settings'),
    ('alert_rules', '{"enabled": true, "max_alerts_per_user_per_day": 10}', 'Alert rules configuration')
ON CONFLICT (config_key) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO aqi_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aqi_user;

-- Comments for documentation
COMMENT ON TABLE model_selections IS 'Stores automatic model selection history for each city/horizon combination';
COMMENT ON TABLE user_feedback IS 'Stores user feedback for UI/UX improvements and alert refinement';
COMMENT ON TABLE alert_rules IS 'Dynamic alert rule configuration';
COMMENT ON TABLE system_config IS 'System-wide configuration with version control';
COMMENT ON TABLE change_log IS 'Audit trail for all system changes';
COMMENT ON TABLE documentation_versions IS 'Version-controlled documentation storage';

COMMENT ON COLUMN predictions.actual_aqi IS 'Actual AQI value observed (for performance tracking)';
COMMENT ON COLUMN predictions.error IS 'Computed absolute error (predicted - actual)';
COMMENT ON COLUMN alerts.rule_id IS 'Reference to the alert rule that triggered this alert';
COMMENT ON COLUMN alerts.acknowledged IS 'Whether user has acknowledged this alert';
