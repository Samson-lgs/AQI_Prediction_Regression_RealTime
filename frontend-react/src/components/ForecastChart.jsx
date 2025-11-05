import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { getAQICategory, getAQIColor, formatTimestamp } from '../utils';

const ForecastChart = ({ data }) => {
  if (!data || !data.predictions || data.predictions.length === 0) {
    return <div className="no-data">No forecast data available</div>;
  }

  // Prepare chart data
  const chartData = data.predictions.map(point => ({
    timestamp: point.timestamp,
    aqi: Math.round(point.aqi),
    lower: point.confidence_lower ? Math.round(point.confidence_lower) : null,
    upper: point.confidence_upper ? Math.round(point.confidence_upper) : null,
    hour: new Date(point.timestamp).getHours()
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="tooltip-time">{formatTimestamp(data.timestamp)}</p>
          <p className="tooltip-aqi" style={{ color: getAQIColor(data.aqi) }}>
            AQI: <strong>{data.aqi}</strong>
          </p>
          <p className="tooltip-category">
            {getAQICategory(data.aqi)}
          </p>
          {data.lower && data.upper && (
            <p className="tooltip-confidence">
              Range: {data.lower} - {data.upper}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  // Custom dot colors based on AQI
  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    const color = getAQIColor(payload.aqi);
    
    return (
      <circle 
        cx={cx} 
        cy={cy} 
        r={4} 
        fill={color} 
        stroke="white" 
        strokeWidth={2}
      />
    );
  };

  return (
    <div className="forecast-chart">
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="aqiGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          <XAxis 
            dataKey="hour"
            tickFormatter={(hour) => `${hour}:00`}
            stroke="#6b7280"
            style={{ fontSize: '0.75rem' }}
          />
          
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '0.75rem' }}
            label={{ value: 'AQI', angle: -90, position: 'insideLeft' }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend 
            wrapperStyle={{ fontSize: '0.875rem' }}
            iconType="circle"
          />

          {/* AQI Category Reference Lines */}
          <ReferenceLine y={50} stroke="#00e400" strokeDasharray="3 3" label={{ value: 'Good', position: 'right', fill: '#00e400' }} />
          <ReferenceLine y={100} stroke="#ffff00" strokeDasharray="3 3" label={{ value: 'Satisfactory', position: 'right', fill: '#ffff00' }} />
          <ReferenceLine y={200} stroke="#ff7e00" strokeDasharray="3 3" label={{ value: 'Moderate', position: 'right', fill: '#ff7e00' }} />
          <ReferenceLine y={300} stroke="#ff0000" strokeDasharray="3 3" label={{ value: 'Poor', position: 'right', fill: '#ff0000' }} />
          
          {/* Confidence Interval */}
          {chartData[0].lower && (
            <Area
              type="monotone"
              dataKey="upper"
              stroke="none"
              fill="#3b82f6"
              fillOpacity={0.1}
            />
          )}
          
          {chartData[0].lower && (
            <Area
              type="monotone"
              dataKey="lower"
              stroke="none"
              fill="white"
              fillOpacity={1}
            />
          )}
          
          {/* Main AQI Line */}
          <Line 
            type="monotone" 
            dataKey="aqi" 
            stroke="#3b82f6" 
            strokeWidth={3}
            dot={<CustomDot />}
            activeDot={{ r: 6 }}
            name="Predicted AQI"
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="forecast-summary">
        <div className="summary-item">
          <span className="summary-label">Average</span>
          <span className="summary-value">
            {Math.round(chartData.reduce((sum, d) => sum + d.aqi, 0) / chartData.length)}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Maximum</span>
          <span className="summary-value">
            {Math.max(...chartData.map(d => d.aqi))}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Minimum</span>
          <span className="summary-value">
            {Math.min(...chartData.map(d => d.aqi))}
          </span>
        </div>
      </div>

      <style jsx>{`
        .forecast-chart {
          padding: 1rem 0;
        }

        .custom-tooltip {
          background: white;
          padding: 1rem;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .tooltip-time {
          font-size: 0.75rem;
          color: #6b7280;
          margin-bottom: 0.5rem;
        }

        .tooltip-aqi {
          font-size: 1rem;
          margin-bottom: 0.25rem;
        }

        .tooltip-category {
          font-size: 0.875rem;
          color: #4b5563;
          margin-bottom: 0.5rem;
        }

        .tooltip-confidence {
          font-size: 0.75rem;
          color: #6b7280;
          padding-top: 0.5rem;
          border-top: 1px solid #e5e7eb;
        }

        .forecast-summary {
          display: flex;
          justify-content: space-around;
          padding: 1rem;
          background: #f9fafb;
          border-radius: 8px;
          margin-top: 1rem;
        }

        .summary-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }

        .summary-label {
          font-size: 0.75rem;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .summary-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #1f2937;
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

export default ForecastChart;
