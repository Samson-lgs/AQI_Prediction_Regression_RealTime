-- Drop database if exists (be careful with this in production!)
DROP DATABASE IF EXISTS aqi_db;

-- Create database
CREATE DATABASE aqi_db;

-- Connect to the database
\c aqi_db

-- Create tables
CREATE TABLE cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE aqi_data (
    data_id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(city_id),
    timestamp TIMESTAMP NOT NULL,
    aqi_value DECIMAL(10, 2) NOT NULL,
    pm2_5 DECIMAL(10, 2),
    pm10 DECIMAL(10, 2),
    no2 DECIMAL(10, 2),
    so2 DECIMAL(10, 2),
    co DECIMAL(10, 2),
    o3 DECIMAL(10, 2),
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    wind_speed DECIMAL(5, 2),
    wind_direction INTEGER,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE predictions (
    prediction_id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(city_id),
    timestamp TIMESTAMP NOT NULL,
    predicted_aqi DECIMAL(10, 2) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_aqi_data_city_timestamp ON aqi_data(city_id, timestamp);
CREATE INDEX idx_predictions_city_timestamp ON predictions(city_id, timestamp);

-- Create a view for latest AQI readings
CREATE VIEW latest_aqi_readings AS
SELECT 
    c.city_name,
    c.state,
    ad.aqi_value,
    ad.pm2_5,
    ad.pm10,
    ad.timestamp,
    ad.created_at
FROM cities c
JOIN (
    SELECT DISTINCT ON (city_id) *
    FROM aqi_data
    ORDER BY city_id, timestamp DESC
) ad ON c.city_id = ad.city_id;

-- Add comments
COMMENT ON TABLE cities IS 'Stores information about Indian cities being monitored';
COMMENT ON TABLE aqi_data IS 'Stores historical AQI and weather data for each city';
COMMENT ON TABLE predictions IS 'Stores AQI predictions made by different models';
COMMENT ON VIEW latest_aqi_readings IS 'Shows the most recent AQI reading for each city';