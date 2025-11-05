import React from 'react';
import { Award, TrendingUp, Target, BarChart3 } from 'lucide-react';

const ModelMetrics = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="card">
        <h2>Model Performance</h2>
        <p className="no-data">No model metrics available</p>
      </div>
    );
  }

  const metrics = [
    {
      key: 'r2_score',
      name: 'R² Score',
      description: 'Goodness of fit (closer to 1 is better)',
      icon: <Award size={24} />,
      format: (val) => val.toFixed(4),
      color: '#3b82f6'
    },
    {
      key: 'rmse',
      name: 'RMSE',
      description: 'Root Mean Squared Error (lower is better)',
      icon: <Target size={24} />,
      format: (val) => val.toFixed(2),
      color: '#8b5cf6'
    },
    {
      key: 'mae',
      name: 'MAE',
      description: 'Mean Absolute Error (lower is better)',
      icon: <BarChart3 size={24} />,
      format: (val) => val.toFixed(2),
      color: '#10b981'
    },
    {
      key: 'mape',
      name: 'MAPE',
      description: 'Mean Absolute Percentage Error',
      icon: <TrendingUp size={24} />,
      format: (val) => `${val.toFixed(2)}%`,
      color: '#f59e0b'
    }
  ];

  // Find best model
  const bestModel = Object.entries(data).reduce((best, [model, metrics]) => {
    if (!best || (metrics.r2_score && metrics.r2_score > (best.metrics.r2_score || 0))) {
      return { model, metrics };
    }
    return best;
  }, null);

  return (
    <div className="card model-metrics">
      <div className="metrics-header">
        <h2>Model Performance</h2>
        {bestModel && (
          <div className="best-model-badge">
            <Award size={16} />
            Best: {bestModel.model}
          </div>
        )}
      </div>

      <div className="models-grid">
        {Object.entries(data).map(([modelName, modelMetrics]) => (
          <div 
            key={modelName} 
            className={`model-card ${bestModel && bestModel.model === modelName ? 'best' : ''}`}
          >
            <h3 className="model-name">{modelName}</h3>
            
            <div className="metrics-list">
              {metrics.map(metric => {
                const value = modelMetrics[metric.key];
                
                if (value === undefined || value === null) {
                  return null;
                }

                return (
                  <div key={metric.key} className="metric-item">
                    <div className="metric-icon" style={{ color: metric.color }}>
                      {metric.icon}
                    </div>
                    <div className="metric-content">
                      <div className="metric-label">
                        {metric.name}
                        <span className="metric-description">{metric.description}</span>
                      </div>
                      <div className="metric-value" style={{ color: metric.color }}>
                        {metric.format(value)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .model-metrics {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .metrics-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .metrics-header h2 {
          color: white;
          margin: 0;
        }

        .best-model-badge {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 9999px;
          font-size: 0.875rem;
          font-weight: 600;
        }

        .models-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .model-card {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          padding: 1.5rem;
          transition: all 0.3s;
        }

        .model-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        }

        .model-card.best {
          border: 2px solid rgba(255, 255, 255, 0.5);
          box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
        }

        .model-name {
          font-size: 1.25rem;
          font-weight: 600;
          margin-bottom: 1rem;
          padding-bottom: 0.75rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .metrics-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .metric-item {
          display: flex;
          gap: 1rem;
          align-items: flex-start;
        }

        .metric-icon {
          padding: 0.5rem;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .metric-content {
          flex: 1;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

        .metric-label {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .metric-description {
          font-size: 0.75rem;
          opacity: 0.8;
        }

        .metric-value {
          font-size: 1.5rem;
          font-weight: 700;
        }

        .no-data {
          text-align: center;
          padding: 3rem;
          color: rgba(255, 255, 255, 0.7);
        }

        @media (max-width: 768px) {
          .models-grid {
            grid-template-columns: 1fr;
          }

          .metrics-header {
            flex-direction: column;
            gap: 1rem;
            align-items: flex-start;
          }
        }
      `}</style>
    </div>
  );
};

export default ModelMetrics;
