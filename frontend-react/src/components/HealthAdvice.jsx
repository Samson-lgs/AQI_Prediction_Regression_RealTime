import React from 'react';
import { AlertCircle, Heart, Wind, Activity } from 'lucide-react';
import { getHealthAdvice, getMaskRecommendation } from '../utils/healthAdvice';

const HealthAdvice = ({ aqi }) => {
  if (!aqi) {
    return (
      <div className="card">
        <div className="card-header">
          <h3>Health Recommendations</h3>
        </div>
        <div className="card-content">
          <p style={{ color: '#6b7280' }}>No AQI data available</p>
        </div>
      </div>
    );
  }

  const advice = getHealthAdvice(aqi);
  if (!advice) return null;

  const maskRec = getMaskRecommendation(aqi);

  return (
    <div className="card">
      <div className="card-header" style={{ borderBottom: `3px solid ${advice.color}` }}>
        <h3>Health Recommendations</h3>
        <div style={{ 
          display: 'inline-block', 
          padding: '0.25rem 0.75rem', 
          borderRadius: '0.5rem',
          backgroundColor: advice.color + '20',
          color: advice.color,
          fontWeight: '600',
          fontSize: '0.875rem'
        }}>
          {advice.category}
        </div>
      </div>
      <div className="card-content" style={{ padding: '1.5rem' }}>
        {/* General Public */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Activity size={20} style={{ color: advice.color }} />
            <h4 style={{ margin: 0, fontSize: '1rem' }}>General Public</h4>
          </div>
          <p style={{ color: '#4b5563', margin: '0.5rem 0' }}>{advice.general}</p>
        </div>

        {/* Sensitive Groups */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Heart size={20} style={{ color: advice.color }} />
            <h4 style={{ margin: 0, fontSize: '1rem' }}>Sensitive Groups</h4>
          </div>
          <p style={{ color: '#4b5563', margin: '0.5rem 0' }}>{advice.sensitive}</p>
        </div>

        {/* Outdoor Activities */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Wind size={20} style={{ color: advice.color }} />
            <h4 style={{ margin: 0, fontSize: '1rem' }}>Outdoor Activities</h4>
          </div>
          <p style={{ color: '#4b5563', margin: '0.5rem 0' }}>{advice.outdoor}</p>
        </div>

        {/* Action Items */}
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <AlertCircle size={20} style={{ color: advice.color }} />
            <h4 style={{ margin: 0, fontSize: '1rem' }}>Recommended Actions</h4>
          </div>
          <ul style={{ 
            listStyle: 'none', 
            padding: 0, 
            margin: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            {advice.actions.map((action, idx) => (
              <li key={idx} style={{ 
                display: 'flex', 
                alignItems: 'flex-start',
                padding: '0.5rem',
                backgroundColor: '#f9fafb',
                borderRadius: '0.375rem',
                fontSize: '0.875rem'
              }}>
                <span style={{ 
                  color: advice.color, 
                  marginRight: '0.5rem',
                  fontWeight: 'bold'
                }}>•</span>
                <span style={{ color: '#374151' }}>{action}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Mask Recommendation */}
        <div style={{ 
          marginTop: '1rem',
          padding: '1rem',
          backgroundColor: aqi > 150 ? '#fef2f2' : '#f0fdf4',
          borderRadius: '0.5rem',
          borderLeft: `4px solid ${advice.color}`
        }}>
          <strong style={{ color: '#111827' }}>Mask Recommendation: </strong>
          <span style={{ color: '#4b5563' }}>{maskRec}</span>
        </div>
      </div>
    </div>
  );
};

export default HealthAdvice;
