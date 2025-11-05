import React, { useEffect, useState } from 'react';
import { useStore } from '../store';

const Compare = () => {
  const { cities, compareCities, cityComparison } = useStore();
  const [selected, setSelected] = useState([]);
  const [days, setDays] = useState(7);

  useEffect(() => {
    if (selected.length >= 2) {
      compareCities(selected, days);
    }
  }, [selected, days, compareCities]);

  const toggleCity = (city) => {
    setSelected(prev => prev.includes(city) ? prev.filter(c => c !== city) : [...prev, city]);
  };

  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h2>Compare Cities</h2>
          <div className="controls">
            <label>
              Days:
              <select value={days} onChange={e => setDays(Number(e.target.value))}>
                {[7, 14, 30].map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </label>
          </div>
        </div>
        <div className="card-content">
          <div className="city-list" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '8px' }}>
            {cities.map(c => (
              <label key={c.name} className={`chip ${selected.includes(c.name) ? 'selected' : ''}`}>
                <input type="checkbox" checked={selected.includes(c.name)} onChange={() => toggleCity(c.name)} />
                {c.name}
              </label>
            ))}
          </div>

          {cityComparison && (
            <div className="comparison-grid" style={{ marginTop: '1rem' }}>
              {Object.entries(cityComparison).map(([city, stats]) => (
                <div key={city} className="card" style={{ marginBottom: '1rem' }}>
                  <div className="card-header"><h3>{city}</h3></div>
                  <div className="card-content">
                    {stats ? (
                      <ul>
                        <li>Avg AQI: {stats.avg_aqi?.toFixed ? stats.avg_aqi.toFixed(1) : stats.avg_aqi}</li>
                        <li>Max AQI: {stats.max_aqi}</li>
                        <li>Min AQI: {stats.min_aqi}</li>
                        <li>Data Points: {stats.data_points}</li>
                      </ul>
                    ) : (
                      <p>No data available</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Compare;
