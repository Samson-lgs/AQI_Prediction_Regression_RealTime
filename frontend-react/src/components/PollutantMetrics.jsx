import React from 'react';
import { getPollutantCategory, getPollutantLimit } from '../utils';

const PollutantMetrics = ({ data }) => {
  if (!data || !data.pollutants) {
    return (
      <div className="card">
        <h2>Pollutant Levels</h2>
        <p className="no-data">No pollutant data available</p>
      </div>
    );
  }

  const pollutants = [
    { key: 'pm25', name: 'PM2.5', unit: 'µg/m³', icon: '🌫️' },
    { key: 'pm10', name: 'PM10', unit: 'µg/m³', icon: '💨' },
    { key: 'no2', name: 'NO₂', unit: 'µg/m³', icon: '🏭' },
    { key: 'so2', name: 'SO₂', unit: 'µg/m³', icon: '⚗️' },
    { key: 'co', name: 'CO', unit: 'mg/m³', icon: '🚗' },
    { key: 'o3', name: 'O₃', unit: 'µg/m³', icon: '☀️' }
  ];

  const getBarColor = (category) => {
    const colors = {
      'Good': '#10b981',
      'Moderate': '#f59e0b',
      'Poor': '#ef4444',
      'Severe': '#7e0023'
    };
    return colors[category] || '#6b7280';
  };

  const getBarWidth = (pollutant, value) => {
    const limits = getPollutantLimit(pollutant);
    const max = limits.severe || 100;
    return Math.min((value / max) * 100, 100);
  };

  return (
    <div className="card pollutant-metrics">
      <h2>Pollutant Levels</h2>
      
      <div className="pollutants-grid">
        {pollutants.map(pollutant => {
          const value = data.pollutants[pollutant.key];
          
          if (value === undefined || value === null) {
            return (
              <div key={pollutant.key} className="pollutant-item">
                <div className="pollutant-header">
                  <span className="pollutant-icon">{pollutant.icon}</span>
                  <span className="pollutant-name">{pollutant.name}</span>
                </div>
                <div className="pollutant-value">--</div>
              </div>
            );
          }

          const category = getPollutantCategory(pollutant.key, value);
          const barColor = getBarColor(category);
          const barWidth = getBarWidth(pollutant.key, value);

          return (
            <div key={pollutant.key} className="pollutant-item">
              <div className="pollutant-header">
                <span className="pollutant-icon">{pollutant.icon}</span>
                <span className="pollutant-name">{pollutant.name}</span>
                <span className="pollutant-category" style={{ color: barColor }}>
                  {category}
                </span>
              </div>
              
              <div className="pollutant-value">
                {value.toFixed(2)} <span className="unit">{pollutant.unit}</span>
              </div>
              
              <div className="pollutant-bar-container">
                <div 
                  className="pollutant-bar" 
                  style={{ 
                    width: `${barWidth}%`,
                    backgroundColor: barColor 
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <style jsx>{`
        .pollutant-metrics h2 {
          margin-bottom: 1.5rem;
        }

        .pollutants-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
        }

        .pollutant-item {
          padding: 1rem;
          background: #f9fafb;
          border-radius: 8px;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .pollutant-item:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .pollutant-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }

        .pollutant-icon {
          font-size: 1.25rem;
        }

        .pollutant-name {
          font-weight: 600;
          color: #1f2937;
          flex: 1;
        }

        .pollutant-category {
          font-size: 0.75rem;
          font-weight: 600;
        }

        .pollutant-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #1f2937;
          margin-bottom: 0.75rem;
        }

        .unit {
          font-size: 0.875rem;
          font-weight: 400;
          color: #6b7280;
        }

        .pollutant-bar-container {
          height: 8px;
          background: #e5e7eb;
          border-radius: 4px;
          overflow: hidden;
        }

        .pollutant-bar {
          height: 100%;
          border-radius: 4px;
          transition: width 0.5s ease;
        }

        .no-data {
          text-align: center;
          padding: 3rem;
          color: #6b7280;
        }

        @media (max-width: 768px) {
          .pollutants-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default PollutantMetrics;
