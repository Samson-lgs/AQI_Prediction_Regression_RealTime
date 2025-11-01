-- Database Schema for AQI Prediction System
-- TODO: Define tables for storing AQI data and predictions

-- Create database
CREATE DATABASE IF NOT EXISTS aqi_prediction;

-- Use the database
\c aqi_prediction;

-- AQI Data Table
CREATE TABLE IF NOT EXISTS aqi_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(255) NOT NULL,
    pm25 FLOAT,
    pm10 FLOAT,
    no2 FLOAT,
    so2 FLOAT,
    co FLOAT,
    o3 FLOAT,
    aqi INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(255) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    predicted_aqi FLOAT,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_aqi_timestamp ON aqi_data(timestamp);
CREATE INDEX idx_aqi_location ON aqi_data(location);
CREATE INDEX idx_pred_timestamp ON predictions(timestamp);
