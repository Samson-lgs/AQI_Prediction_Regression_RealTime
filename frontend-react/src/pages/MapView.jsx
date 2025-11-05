import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useStore } from '../store';
import { CITY_COORDINATES, getAQIColor } from '../cityCoordinates';

const MapView = () => {
  const { allCitiesCurrent, fetchAllCitiesCurrent } = useStore();

  useEffect(() => {
    fetchAllCitiesCurrent();
    const id = setInterval(fetchAllCitiesCurrent, 60_000);
    return () => clearInterval(id);
  }, [fetchAllCitiesCurrent]);

  const indiaCenter = [22.9734, 78.6569];

  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h2>Real-time AQI Map</h2>
          <p>Bubble color reflects AQI level. Hover for details.</p>
        </div>
        <div className="card-content" style={{ height: '70vh' }}>
          <MapContainer center={indiaCenter} zoom={5} scrollWheelZoom style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {allCitiesCurrent.map((row, idx) => {
              const coords = CITY_COORDINATES[row.city] || CITY_COORDINATES[row.city?.replace(/\s+/g, '')];
              if (!coords) return null;
              const color = getAQIColor(row.aqi);
              const radius = Math.max(6, Math.min(18, (row.aqi || 0) / 20));
              return (
                <CircleMarker key={row.city + idx} center={coords} radius={radius} pathOptions={{ color, fillColor: color, fillOpacity: 0.6 }}>
                  <Tooltip direction="top" offset={[0, -2]} opacity={1}>
                    <div>
                      <strong>{row.city}</strong><br />
                      AQI: {row.aqi ?? 'N/A'}<br />
                      PM2.5: {row.pm25 ?? 'N/A'}<br />
                      Updated: {new Date(row.timestamp).toLocaleString()}
                    </div>
                  </Tooltip>
                </CircleMarker>
              );
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
};

export default MapView;
