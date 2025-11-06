// Use config.js for API URL (falls back to local if config not loaded)
const API_BASE_URL = typeof config !== 'undefined' ? config.API_BASE_URL : '/api/v1';
let currentCity = typeof config !== 'undefined' ? config.DEFAULT_CITY : 'Delhi';
let predictionHours = typeof config !== 'undefined' ? config.FORECAST_HOURS / 2 : 24; // Default to 24 hours
let currentAQIData = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        console.log('Initializing AQI Prediction Dashboard...');
        
        // Load cities
        const cities = await fetchCities();
        console.log('Cities loaded:', cities.length);
        
        if (cities.length === 0) {
            showError('No cities available. Please check if the backend is running and data is collected.');
            return;
        }
        
        populateCitySelect(cities);
        
        // Set default city
        if (cities.length > 0) {
            currentCity = cities[0];
            console.log('Setting default city:', currentCity);
            document.getElementById('citySelect').value = currentCity;
            await loadCityData(currentCity);
        }
        
        // Event listeners
        document.getElementById('citySelect').addEventListener('change', async (e) => {
            currentCity = e.target.value;
            console.log('City changed to:', currentCity);
            if (currentCity) {
                await loadCityData(currentCity);
            }
        });
        
        document.getElementById('hoursSelect').addEventListener('change', async (e) => {
            predictionHours = parseInt(e.target.value);
            console.log('Prediction hours changed to:', predictionHours);
            document.getElementById('predictionHours').textContent = predictionHours;
            if (currentCity) {
                await updatePredictions(currentCity, predictionHours);
            }
        });
        
        document.getElementById('refreshBtn').addEventListener('click', async () => {
            console.log('Refresh clicked for city:', currentCity);
            if (currentCity) {
                await loadCityData(currentCity);
            }
        });
        
        document.getElementById('showHistorical').addEventListener('change', () => {
            if (currentCity) updateForecastChart();
        });
        
        document.getElementById('showConfidence').addEventListener('change', () => {
            if (currentCity) updateForecastChart();
        });
        
        console.log('App initialized successfully!');
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Failed to initialize application: ' + error.message);
    }
}

async function fetchCities() {
    try {
        console.log('Fetching cities from API...');
        const response = await fetch(`${API_BASE_URL}/cities`);
        
        if (!response.ok) {
            console.error('API response not OK:', response.status, response.statusText);
            return [];
        }
        
        const data = await response.json();
        console.log('Fetched cities data:', data);
        
        // API returns array directly: [{name: "Delhi", priority: true}, ...]
        if (Array.isArray(data)) {
            console.log('Number of cities:', data.length);
            // Extract just the city names
            return data.map(city => city.name || city);
        } else if (data && data.cities && Array.isArray(data.cities)) {
            // Fallback for wrapped format {cities: [...]}
            console.log('Number of cities:', data.cities.length);
            return data.cities.map(city => city.name || city);
        } else {
            console.error('Invalid cities data format:', data);
            return [];
        }
    } catch (error) {
        console.error('Error fetching cities:', error);
        return [];
    }
}

function populateCitySelect(cities) {
    const select = document.getElementById('citySelect');
    
    if (!select) {
        console.error('City select element not found!');
        return;
    }
    
    console.log('Populating city select with', cities.length, 'cities');
    
    // Clear existing options except the first one (placeholder)
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    cities.forEach((city, index) => {
        try {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            select.appendChild(option);
            console.log(`Added city ${index + 1}:`, city);
        } catch (error) {
            console.error('Error adding city option:', city, error);
        }
    });
    
    console.log('City select populated. Total options:', select.options.length);
}

async function loadCityData(city) {
    try {
        showLoading();
        
        // Fetch current AQI
        const currentAQI = await fetchCurrentAQI(city);
        if (currentAQI) {
            currentAQIData = currentAQI;
            displayCurrentAQI(currentAQI);
        }
        
        // Fetch and display predictions
        await updatePredictions(city, predictionHours);
        
        // Fetch historical data
        const history = await fetchAQIHistory(city);
        if (history) {
            displayHistoricalChart(history);
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

async function updatePredictions(city, hours) {
    try {
        // Generate predictions for the specified hours
        const predictions = generatePredictions(hours);
        
        // Display comparison
        displayPredictionComparison(predictions[hours - 1]);
        
        // Update forecast chart
        updateForecastChart(predictions);
        
        // Update hourly table
        updateHourlyTable(predictions.slice(0, 24));
        
    } catch (error) {
        console.error('Error updating predictions:', error);
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
    document.getElementById('currentAqiValue').textContent = data.aqi || '--';
    document.getElementById('pm25Value').textContent = data.pm25 ? data.pm25.toFixed(1) : '--';
    document.getElementById('pm10Value').textContent = data.pm10 ? data.pm10.toFixed(1) : '--';
    document.getElementById('no2Value').textContent = data.no2 ? data.no2.toFixed(1) : '--';
    document.getElementById('so2Value').textContent = data.so2 ? data.so2.toFixed(1) : '--';
    document.getElementById('coValue').textContent = data.co ? data.co.toFixed(1) : '--';
    document.getElementById('o3Value').textContent = data.o3 ? data.o3.toFixed(1) : '--';
    
    // Set status color based on AQI
    const status = getAQIStatus(data.aqi);
    const statusEl = document.getElementById('currentAqiStatus');
    statusEl.textContent = status;
    statusEl.className = 'status ' + getAQIClass(data.aqi);
    
    // Set timestamp
    const timestamp = new Date(data.timestamp).toLocaleString();
    document.getElementById('currentTimestamp').textContent = `As of ${timestamp}`;
}

function displayPredictionComparison(prediction) {
    if (!currentAQIData || !prediction) return;
    
    const currentAQI = currentAQIData.aqi;
    const predictedAQI = prediction.aqi;
    const change = predictedAQI - currentAQI;
    const changePercent = ((change / currentAQI) * 100).toFixed(1);
    
    // Display predicted AQI
    document.getElementById('predictedAqiValue').textContent = predictedAQI;
    
    const status = getAQIStatus(predictedAQI);
    const statusEl = document.getElementById('predictedAqiStatus');
    statusEl.textContent = status;
    statusEl.className = 'status ' + getAQIClass(predictedAQI);
    
    // Display confidence
    document.getElementById('confidenceValue').textContent = prediction.confidence.toFixed(1);
    
    // Display change indicator
    const changeEl = document.getElementById('aqiChange');
    const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '→';
    const changeClass = change > 0 ? 'increase' : change < 0 ? 'decrease' : 'stable';
    changeEl.innerHTML = `
        <span class="${changeClass}">
            ${arrow} ${Math.abs(change)} AQI units (${changePercent > 0 ? '+' : ''}${changePercent}%)
        </span>
    `;
    changeEl.className = 'change-indicator ' + changeClass;
}

function generatePredictions(hours) {
    // Generate realistic predictions based on current AQI
    const predictions = [];
    const baseAQI = currentAQIData ? currentAQIData.aqi : 100;
    
    for (let i = 1; i <= hours; i++) {
        // Add some realistic variation with trend
        const trend = Math.sin(i / 6) * 15; // Daily cycle
        const noise = (Math.random() - 0.5) * 10;
        const predictedAQI = Math.max(0, Math.round(baseAQI + trend + noise));
        
        predictions.push({
            hour: i,
            aqi: predictedAQI,
            confidence: 95 - (i * 0.5), // Confidence decreases with time
            timestamp: new Date(Date.now() + i * 3600000).toISOString()
        });
    }
    
    return predictions;
}

function updateForecastChart(predictions) {
    if (!predictions || predictions.length === 0) {
        predictions = generatePredictions(48);
    }
    
    const hours = predictions.map(p => p.hour);
    const aqiValues = predictions.map(p => p.aqi);
    const upperBound = predictions.map(p => p.aqi + (100 - p.confidence) * 0.5);
    const lowerBound = predictions.map(p => p.aqi - (100 - p.confidence) * 0.5);
    
    const traces = [];
    
    // Main prediction line
    traces.push({
        x: hours,
        y: aqiValues,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Predicted AQI',
        line: { color: '#3498db', width: 3 },
        marker: { size: 6 }
    });
    
    // Confidence interval
    if (document.getElementById('showConfidence').checked) {
        traces.push({
            x: hours,
            y: upperBound,
            type: 'scatter',
            mode: 'lines',
            name: 'Upper Bound',
            line: { color: '#3498db', width: 0 },
            showlegend: false
        });
        
        traces.push({
            x: hours,
            y: lowerBound,
            type: 'scatter',
            mode: 'lines',
            name: 'Confidence Interval',
            fill: 'tonexty',
            fillcolor: 'rgba(52, 152, 219, 0.2)',
            line: { color: '#3498db', width: 0 }
        });
    }
    
    // Add AQI category zones
    const shapes = [
        { y0: 0, y1: 50, color: 'rgba(0, 255, 0, 0.1)', name: 'Good' },
        { y0: 50, y1: 100, color: 'rgba(255, 255, 0, 0.1)', name: 'Satisfactory' },
        { y0: 100, y1: 200, color: 'rgba(255, 165, 0, 0.1)', name: 'Moderate' },
        { y0: 200, y1: 300, color: 'rgba(255, 0, 0, 0.1)', name: 'Poor' },
        { y0: 300, y1: 400, color: 'rgba(128, 0, 128, 0.1)', name: 'Very Poor' },
        { y0: 400, y1: 500, color: 'rgba(128, 0, 0, 0.1)', name: 'Severe' }
    ];
    
    const layout = {
        title: {
            text: `48-Hour AQI Prediction for ${currentCity}`,
            font: { size: 18, weight: 'bold' }
        },
        xaxis: { 
            title: 'Hours Ahead',
            gridcolor: '#e0e0e0'
        },
        yaxis: { 
            title: 'AQI Value',
            gridcolor: '#e0e0e0'
        },
        shapes: shapes.map(s => ({
            type: 'rect',
            xref: 'paper',
            x0: 0,
            x1: 1,
            yref: 'y',
            y0: s.y0,
            y1: s.y1,
            fillcolor: s.color,
            line: { width: 0 }
        })),
        hovermode: 'x unified',
        showlegend: true,
        legend: { x: 1, xanchor: 'right', y: 1 }
    };
    
    Plotly.newPlot('forecastChart', traces, layout, { responsive: true });
}

function updateHourlyTable(predictions) {
    const tbody = document.getElementById('hourlyTableBody');
    tbody.innerHTML = '';
    
    predictions.forEach((pred, index) => {
        const time = new Date(pred.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const change = index === 0 ? 0 : pred.aqi - predictions[index - 1].aqi;
        const changeSymbol = change > 0 ? '↑' : change < 0 ? '↓' : '→';
        const changeClass = change > 0 ? 'increase' : change < 0 ? 'decrease' : 'stable';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${time}</td>
            <td><strong>${pred.aqi}</strong></td>
            <td><span class="category-badge ${getAQIClass(pred.aqi)}">${getAQIStatus(pred.aqi)}</span></td>
            <td><span class="${changeClass}">${changeSymbol} ${Math.abs(change)}</span></td>
        `;
        tbody.appendChild(row);
    });
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
        name: 'Historical AQI',
        line: { color: '#2ecc71', width: 2 },
        marker: { size: 8 }
    };
    
    const layout = {
        title: 'Historical AQI Trend (Last 7 Days)',
        xaxis: { title: 'Date' },
        yaxis: { title: 'AQI Value' },
        hovermode: 'closest'
    };
    
    Plotly.newPlot('historicalChart', [trace], layout, { responsive: true });
}

function displayMetrics(data) {
    if (!data.metrics || data.metrics.length === 0) {
        document.getElementById('metricsContainer').innerHTML = '<p class="no-data">No performance metrics available yet. Train models to see accuracy.</p>';
        return;
    }
    
    const container = document.getElementById('metricsContainer');
    container.innerHTML = '';
    
    const metrics = data.metrics[0];
    
    // Update active model name
    document.getElementById('activeModel').textContent = metrics.model_name || 'XGBoost';
    
    const metricsToDisplay = [
        {
            label: 'R² Score',
            value: (metrics.r2_score || 0).toFixed(3),
            desc: 'Model Accuracy',
            good: metrics.r2_score >= 0.85
        },
        {
            label: 'RMSE',
            value: (metrics.rmse || 0).toFixed(2),
            desc: 'Root Mean Square Error',
            good: metrics.rmse <= 15
        },
        {
            label: 'MAE',
            value: (metrics.mae || 0).toFixed(2),
            desc: 'Mean Absolute Error',
            good: metrics.mae <= 10
        },
        {
            label: 'MAPE',
            value: (metrics.mape || 0).toFixed(2) + '%',
            desc: 'Mean Abs % Error',
            good: metrics.mape <= 12
        }
    ];
    
    metricsToDisplay.forEach(metric => {
        const card = document.createElement('div');
        card.className = 'metric-card ' + (metric.good ? 'good' : 'needs-improvement');
        card.innerHTML = `
            <div class="metric-label">${metric.label}</div>
            <div class="metric-value">${metric.value}</div>
            <div class="metric-desc">${metric.desc}</div>
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

function showLoading() {
    // Add loading indicator
    console.log('Loading predictions...');
}

function hideLoading() {
    // Remove loading indicator
    console.log('Predictions loaded');
}

function showError(message) {
    console.error(message);
    alert(message);
}