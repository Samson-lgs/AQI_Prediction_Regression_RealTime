import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useStore } from '../store';
import CitySelector from './CitySelector';
import AQICard from './AQICard';
import ForecastChart from './ForecastChart';
import PollutantMetrics from './PollutantMetrics';
import ModelMetrics from './ModelMetrics';
import HistoricalChart from './HistoricalChart';
import HealthAdvice from './HealthAdvice';
import { AlertCircle, Loader } from 'lucide-react';

const Dashboard = () => {
  const { cityId } = useParams();
  const { 
    selectedCity, 
    currentAQI, 
    forecast, 
    historicalData,
    modelMetrics,
    loading, 
    error,
    loadCityData 
  } = useStore();

  useEffect(() => {
    if (selectedCity) {
      loadCityData(selectedCity);
    }
  }, [selectedCity, loadCityData]);

  if (loading && !currentAQI) {
    return (
      <div className="loading-container">
        <Loader className="spinner" size={48} />
        <p>Loading air quality data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <AlertCircle size={48} color="#ef4444" />
        <h2>Error Loading Data</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!selectedCity) {
    return (
      <div className="empty-state">
        <h2>Welcome to AQI Prediction System</h2>
        <p>Select a city to view real-time air quality data and forecasts</p>
        <CitySelector />
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Air Quality Dashboard</h1>
        <CitySelector />
      </div>

      <div className="dashboard-grid">
        {/* Current AQI Section */}
        <div className="grid-section current-aqi">
          <AQICard data={currentAQI} />
        </div>

        {/* Pollutant Metrics */}
        <div className="grid-section pollutants">
          <PollutantMetrics data={currentAQI} />
        </div>

        {/* Health Advice */}
        <div className="grid-section health-advice">
          <HealthAdvice aqi={currentAQI?.aqi} />
        </div>

        {/* Forecast Chart */}
        <div className="grid-section forecast">
          <div className="card">
            <h2>48-Hour Forecast</h2>
            {forecast && forecast.predictions ? (
              <ForecastChart data={forecast} />
            ) : (
              <div className="no-data">No forecast data available</div>
            )}
          </div>
        </div>

        {/* Historical Trend */}
        <div className="grid-section historical">
          <div className="card">
            <h2>Historical Trend (24 Hours)</h2>
            {historicalData && historicalData.length > 0 ? (
              <HistoricalChart data={historicalData} />
            ) : (
              <div className="no-data">No historical data available</div>
            )}
          </div>
        </div>

        {/* Model Performance */}
        <div className="grid-section models">
          <ModelMetrics data={modelMetrics} />
        </div>
      </div>

      <style jsx>{`
        .dashboard {
          max-width: 1400px;
          margin: 0 auto;
          padding: 2rem;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
        }

        .dashboard-header h1 {
          font-size: 2rem;
          color: #1f2937;
          margin: 0;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(12, 1fr);
          gap: 1.5rem;
        }

        .grid-section {
          animation: fadeIn 0.5s ease-in;
        }

        .current-aqi {
          grid-column: span 4;
        }

        .pollutants {
          grid-column: span 8;
        }

        .health-advice {
          grid-column: span 4;
        }

        .forecast {
          grid-column: span 8;
        }

        .historical {
          grid-column: span 4;
        }

        .models {
          grid-column: span 12;
        }

        .loading-container,
        .error-container,
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 60vh;
          text-align: center;
          padding: 2rem;
        }

        .loading-container p,
        .error-container p,
        .empty-state p {
          color: #6b7280;
          margin-top: 1rem;
        }

        .error-container h2 {
          color: #1f2937;
          margin-top: 1rem;
        }

        .empty-state h2 {
          font-size: 1.5rem;
          color: #1f2937;
          margin-bottom: 0.5rem;
        }

        .no-data {
          text-align: center;
          padding: 3rem;
          color: #6b7280;
        }

        @media (max-width: 1024px) {
          .current-aqi,
          .pollutants,
          .health-advice,
          .forecast,
          .historical,
          .models {
            grid-column: span 12;
          }
        }

        @media (max-width: 768px) {
          .dashboard {
            padding: 1rem;
          }

          .dashboard-header {
            flex-direction: column;
            gap: 1rem;
            align-items: stretch;
          }

          .dashboard-header h1 {
            font-size: 1.5rem;
          }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
