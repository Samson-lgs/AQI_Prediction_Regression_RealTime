import React from 'react';
import { Wind, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getAQICategory, getAQIColor, getAQIDescription, formatTimestamp, getTrendIcon } from '../utils';

const AQICard = ({ data }) => {
  if (!data) {
    return (
      <div className="card aqi-card">
        <p className="no-data">No AQI data available</p>
      </div>
    );
  }

  const aqi = data.aqi || 0;
  const category = getAQICategory(aqi);
  const color = getAQIColor(aqi);
  const description = getAQIDescription(aqi);
  const trend = data.trend || 0;

  const getTrendComponent = () => {
    if (trend > 5) return <TrendingUp size={20} color="#ef4444" />;
    if (trend < -5) return <TrendingDown size={20} color="#10b981" />;
    return <Minus size={20} color="#6b7280" />;
  };

  return (
    <div className="card aqi-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="aqi-header">
        <Wind size={32} color={color} />
        <span className="aqi-label">Current AQI</span>
      </div>

      <div className="aqi-value" style={{ color }}>
        {Math.round(aqi)}
      </div>

      <div className="aqi-category">
        <span className="badge" style={{ 
          background: `${color}20`,
          color: color,
          border: `1px solid ${color}40`
        }}>
          {category}
        </span>
      </div>

      <div className="aqi-trend">
        {getTrendComponent()}
        <span>{Math.abs(trend).toFixed(1)} from previous hour</span>
      </div>

      <div className="aqi-description">
        {description}
      </div>

      {data.timestamp && (
        <div className="aqi-timestamp">
          Updated: {formatTimestamp(data.timestamp)}
        </div>
      )}

      <style jsx>{`
        .aqi-card {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          min-height: 400px;
        }

        .aqi-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .aqi-label {
          font-size: 0.875rem;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          font-weight: 600;
        }

        .aqi-value {
          font-size: 4rem;
          font-weight: 700;
          line-height: 1;
          margin: 1rem 0;
        }

        .aqi-category {
          margin: 0.5rem 0;
        }

        .aqi-category .badge {
          display: inline-block;
          padding: 0.5rem 1rem;
          border-radius: 9999px;
          font-size: 0.875rem;
          font-weight: 600;
        }

        .aqi-trend {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #6b7280;
          font-size: 0.875rem;
        }

        .aqi-description {
          color: #4b5563;
          line-height: 1.5;
          padding: 1rem;
          background: #f9fafb;
          border-radius: 8px;
          margin-top: auto;
        }

        .aqi-timestamp {
          color: #9ca3af;
          font-size: 0.75rem;
          text-align: center;
          padding-top: 1rem;
          border-top: 1px solid #e5e7eb;
        }

        .no-data {
          text-align: center;
          padding: 3rem;
          color: #6b7280;
        }

        @media (max-width: 768px) {
          .aqi-value {
            font-size: 3rem;
          }
        }
      `}</style>
    </div>
  );
};

export default AQICard;
