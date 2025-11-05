import React, { useEffect, useState } from 'react';
import { useStore } from '../store';

const Rankings = () => {
  const { rankings, fetchRankings } = useStore();
  const [days, setDays] = useState(7);
  const [metric, setMetric] = useState('avg_aqi');

  useEffect(() => {
    fetchRankings(days, metric);
  }, [days, metric, fetchRankings]);

  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h2>City Rankings</h2>
          <div className="controls">
            <label>
              Days:
              <select value={days} onChange={e => setDays(Number(e.target.value))}>
                {[7, 14, 30].map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </label>
            <label>
              Metric:
              <select value={metric} onChange={e => setMetric(e.target.value)}>
                <option value="avg_aqi">Avg AQI</option>
                <option value="max_aqi">Max AQI</option>
                <option value="avg_pm25">Avg PM2.5</option>
              </select>
            </label>
          </div>
        </div>
        <div className="card-content">
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>City</th>
                <th>Avg AQI</th>
                <th>Max AQI</th>
                <th>Avg PM2.5</th>
                <th>Data Points</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((r, idx) => (
                <tr key={r.city + idx}>
                  <td>{idx + 1}</td>
                  <td>{r.city}</td>
                  <td>{r.avg_aqi?.toFixed ? r.avg_aqi.toFixed(1) : r.avg_aqi}</td>
                  <td>{r.max_aqi}</td>
                  <td>{r.avg_pm25?.toFixed ? r.avg_pm25.toFixed(1) : r.avg_pm25}</td>
                  <td>{r.data_points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Rankings;
