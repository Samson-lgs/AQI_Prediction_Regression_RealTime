import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getAQIColor, formatTime } from '../utils';

const HistoricalChart = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="no-data">No historical data available</div>;
  }

  // Prepare chart data
  const chartData = data.map(point => ({
    timestamp: point.timestamp,
    aqi: Math.round(point.aqi || 0),
    time: formatTime(point.timestamp)
  })).reverse(); // Show oldest to newest

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="tooltip-time">{data.time}</p>
          <p className="tooltip-aqi" style={{ color: getAQIColor(data.aqi) }}>
            AQI: <strong>{data.aqi}</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  // Calculate statistics
  const aqiValues = chartData.map(d => d.aqi);
  const avgAQI = Math.round(aqiValues.reduce((a, b) => a + b, 0) / aqiValues.length);
  const maxAQI = Math.max(...aqiValues);
  const minAQI = Math.min(...aqiValues);
  const trend = aqiValues[aqiValues.length - 1] - aqiValues[0];

  return (
    <div className="historical-chart">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          <XAxis 
            dataKey="time"
            stroke="#6b7280"
            style={{ fontSize: '0.75rem' }}
            interval="preserveStartEnd"
          />
          
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '0.75rem' }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Line 
            type="monotone" 
            dataKey="aqi" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ r: 3, fill: '#3b82f6' }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="historical-stats">
        <div className="stat-item">
          <span className="stat-label">Average</span>
          <span className="stat-value" style={{ color: getAQIColor(avgAQI) }}>
            {avgAQI}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">High</span>
          <span className="stat-value" style={{ color: getAQIColor(maxAQI) }}>
            {maxAQI}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Low</span>
          <span className="stat-value" style={{ color: getAQIColor(minAQI) }}>
            {minAQI}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Trend</span>
          <span className="stat-value" style={{ color: trend >= 0 ? '#ef4444' : '#10b981' }}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}
          </span>
        </div>
      </div>

      <style jsx>{`
        .historical-chart {
          padding: 1rem 0;
        }

        .custom-tooltip {
          background: white;
          padding: 0.75rem;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .tooltip-time {
          font-size: 0.75rem;
          color: #6b7280;
          margin-bottom: 0.25rem;
        }

        .tooltip-aqi {
          font-size: 0.875rem;
          margin: 0;
        }

        .historical-stats {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 0.75rem;
          margin-top: 1rem;
          padding: 1rem;
          background: #f9fafb;
          border-radius: 8px;
        }

        .stat-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
        }

        .stat-label {
          font-size: 0.75rem;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .stat-value {
          font-size: 1.25rem;
          font-weight: 700;
        }

        .no-data {
          text-align: center;
          padding: 3rem;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
};

export default HistoricalChart;
