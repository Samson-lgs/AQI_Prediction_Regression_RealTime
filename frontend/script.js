const API_BASE_URL = '/api/v1';
let currentCity = '';

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Load cities
        const cities = await fetchCities();
        populateCitySelect(cities);
        
        // Set default city
        if (cities.length > 0) {
            currentCity = cities[0];
            document.getElementById('citySelect').value = currentCity;
            await loadCityData(currentCity);
        }
        
        // Event listeners
        document.getElementById('citySelect').addEventListener('change', async (e) => {
            currentCity = e.target.value;
            if (currentCity) {
                await loadCityData(currentCity);
            }
        });
        
        document.getElementById('refreshBtn').addEventListener('click', async () => {
            if (currentCity) {
                await loadCityData(currentCity);
            }
        });
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Failed to initialize application');
    }
}

async function fetchCities() {
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        const data = await response.json();
        return data.cities;
    } catch (error) {
        console.error('Error fetching cities:', error);
        return [];
    }
}

function populateCitySelect(cities) {
    const select = document.getElementById('citySelect');
    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        select.appendChild(option);
    });
}

async function loadCityData(city) {
    try {
        showLoading();
        
        // Fetch current AQI
        const currentAQI = await fetchCurrentAQI(city);
        if (currentAQI) {
            displayCurrentAQI(currentAQI);
        }
        
        // Fetch historical data
        const history = await fetchAQIHistory(city);
        if (history) {
            displayHistoricalChart(history);
        }
        
        // Fetch forecast
        const forecast = await fetchForecast(city);
        if (forecast) {
            displayForecastChart(forecast);
        }
        
        // Fetch metrics
        const metrics = await fetchMetrics(city);
        if (metrics) {
            displayMetrics(metrics);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading city data:', error);
        showError('Failed to load data for ' + city);
        hideLoading();
    }
}

async function fetchCurrentAQI(city) {
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/current/${city}`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Error fetching current AQI:', error);
        return null;
    }
}

async function fetchAQIHistory(city) {
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/history/${city}?days=7`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Error fetching history:', error);
        return null;
    }
}

async function fetchForecast(city) {
    try {
        const response = await fetch(`${API_BASE_URL}/forecast/${city}`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Error fetching forecast:', error);
        return null;
    }
}

async function fetchMetrics(city) {
    try {
        const response = await fetch(`${API_BASE_URL}/metrics/${city}`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Error fetching metrics:', error);
        return null;
    }
}

function displayCurrentAQI(data) {
    document.getElementById('aqiValue').textContent = data.aqi || '--';
    document.getElementById('pm25Value').textContent = data.pm25 ? data.pm25.toFixed(1) : '--';
    document.getElementById('pm10Value').textContent = data.pm10 ? data.pm10.toFixed(1) : '--';
    document.getElementById('no2Value').textContent = data.no2 ? data.no2.toFixed(1) : '--';
    document.getElementById('so2Value').textContent = data.so2 ? data.so2.toFixed(1) : '--';
    
    // Set status color based on AQI
    const status = getAQIStatus(data.aqi);
    const statusEl = document.getElementById('aqiStatus');
    statusEl.textContent = status;
    statusEl.className = 'aqi-status ' + getAQIClass(data.aqi);
}

function displayHistoricalChart(data) {
    if (!data.data || data.data.length === 0) return;
    
    const timestamps = data.data.map(d => new Date(d.timestamp).toLocaleDateString());
    const aqiValues = data.data.map(d => d.aqi_value);
    
    const trace = {
        x: timestamps,
        y: aqiValues,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'AQI',
        line: { color: '#3498db', width: 2 },
        marker: { size: 8 }
    };
    
    const layout = {
        title: 'Historical AQI Trend',
        xaxis: { title: 'Date' },
        yaxis: { title: 'AQI Value' },
        responsive: true
    };
    
    Plotly.newPlot('historicalChart', [trace], layout);
}

function displayForecastChart(data) {
    // Simulate forecast data
    const hours = Array.from({length: 48}, (_, i) => i);
    const forecastValues = generateSimulatedForecast(48);
    
    const trace = {
        x: hours,
        y: forecastValues,
        type: 'scatter',
        mode: 'lines',
        name: 'Forecast',
        fill: 'tozeroy',
        line: { color: '#2ecc71', width: 2 }
    };
    
    const layout = {
        title: '48-Hour AQI Forecast',
        xaxis: { title: 'Hours Ahead' },
        yaxis: { title: 'Predicted AQI' },
        responsive: true
    };
    
    Plotly.newPlot('forecastChart', [trace], layout);
}

function displayMetrics(data) {
    if (!data.metrics || data.metrics.length === 0) return;
    
    const container = document.getElementById('metricsContainer');
    container.innerHTML = '';
    
    const metrics = data.metrics[0];
    
    const metricsToDisplay = [
        {label: 'R² Score', value: (metrics.r2_score || 0).toFixed(3)},
        {label: 'RMSE', value: (metrics.rmse || 0).toFixed(2)},
        {label: 'MAE', value: (metrics.mae || 0).toFixed(2)},
        {label: 'MAPE', value: (metrics.mape || 0).toFixed(2) + '%'}
    ];
    
    metricsToDisplay.forEach(metric => {
        const card = document.createElement('div');
        card.className = 'metric-card';
        card.innerHTML = `
            <div class="metric-label">${metric.label}</div>
            <div class="metric-value">${metric.value}</div>
        `;
        container.appendChild(card);
    });
}

function getAQIStatus(value) {
    if (value <= 50) return 'Good';
    if (value <= 100) return 'Satisfactory';
    if (value <= 200) return 'Moderately Polluted';
    if (value <= 300) return 'Poor';
    if (value <= 400) return 'Very Poor';
    return 'Severe';
}

function getAQIClass(value) {
    if (value <= 50) return 'good';
    if (value <= 100) return 'satisfactory';
    if (value <= 200) return 'moderate';
    if (value <= 300) return 'poor';
    if (value <= 400) return 'very-poor';
    return 'severe';
}

function generateSimulatedForecast(hours) {
    // Generate realistic forecast data
    return Array.from({length: hours}, () => Math.random() * 100 + 50);
}

function showLoading() {
    // Add loading indicator
    console.log('Loading...');
}

function hideLoading() {
    // Remove loading indicator
    console.log('Loading complete');
}

function showError(message) {
    console.error(message);
    alert(message);
}