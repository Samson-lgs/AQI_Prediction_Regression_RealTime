/* ============================================================================
   UNIFIED AQI SYSTEM APPLICATION
   ============================================================================ */

// Global State
let currentMap = null;
let selectedCities = [];
let currentData = null;
let predictionData = null;

// ============================================================================
// NAVIGATION
// ============================================================================

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.classList.add('active');
    }
    
    // Activate nav link
    const navLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (navLink) {
        navLink.classList.add('active');
    }
    
    // Initialize section-specific features
    if (sectionName === 'home') {
        loadHomeStats();
        loadTopCities();
    } else if (sectionName === 'live') {
        initializeDashboard();
    } else if (sectionName === 'forecast') {
        loadDefaultCity();
    }
}

// ============================================================================
// HOME SECTION
// ============================================================================

async function loadHomeStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        const cities = await response.json();
        
        // Update total cities
        document.getElementById('totalCities').textContent = cities.length;
        
        // Get current AQI for all cities and calculate average
        const aqiPromises = cities.map(city => 
            fetch(`${API_BASE_URL}/aqi/current/${city.name}`).then(r => r.json())
        );
        
        const allAqi = await Promise.all(aqiPromises);
        const validAqi = allAqi.filter(data => data && data.aqi);
        
        if (validAqi.length > 0) {
            const avgAqi = Math.round(
                validAqi.reduce((sum, data) => sum + data.aqi, 0) / validAqi.length
            );
            document.getElementById('currentAvgAQI').textContent = avgAqi;
        }
        
        // Update data sources (hardcoded as per system design)
        document.getElementById('dataSources').textContent = '3';
        
        // Update active alerts (mock for now)
        document.getElementById('activeAlerts').textContent = '0';
        
    } catch (error) {
        console.error('Error loading home stats:', error);
    }
}

async function loadTopCities() {
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        const cities = await response.json();
        
        // Get AQI for all cities
        const cityDataPromises = cities.slice(0, 8).map(async city => {
            try {
                const aqiResponse = await fetch(`${API_BASE_URL}/aqi/current/${city.name}`);
                const aqiData = await aqiResponse.json();
                return {
                    name: city.name,
                    aqi: aqiData.aqi || 0,
                    category: getAQICategory(aqiData.aqi || 0)
                };
            } catch (error) {
                return null;
            }
        });
        
        const cityData = (await Promise.all(cityDataPromises)).filter(d => d !== null);
        
        // Sort by AQI descending
        cityData.sort((a, b) => b.aqi - a.aqi);
        
        // Display in grid
        const grid = document.getElementById('topCitiesGrid');
        grid.innerHTML = cityData.map(city => `
            <div class="city-card" onclick="viewCityDetails('${city.name}')">
                <div class="city-name">${city.name}</div>
                <div class="aqi-display ${getAQIColorClass(city.aqi)}">${city.aqi}</div>
                <div style="text-align: center; font-size: 0.9em; color: #666;">
                    ${city.category}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading top cities:', error);
        document.getElementById('topCitiesGrid').innerHTML = 
            '<div class="error">Unable to load city data</div>';
    }
}

function viewCityDetails(cityName) {
    // Switch to live dashboard and load city data
    showSection('live');
    switchTab('map');
    
    // Center map on city if available
    if (currentMap) {
        getCityCoordinates(cityName).then(coords => {
            if (coords) {
                currentMap.setView([coords.lat, coords.lon], 10);
            }
        });
    }
}

// ============================================================================
// LIVE DASHBOARD SECTION
// ============================================================================

function initializeDashboard() {
    if (!currentMap) {
        initializeMap();
        loadUserAlerts();
        loadHistoricalTrends();
        loadComparison();
    }
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[onclick="switchTab('${tabName}')"]`)?.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.dashboard-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`)?.classList.add('active');
    
    // Resize map if switching to map tab
    if (tabName === 'map' && currentMap) {
        setTimeout(() => currentMap.invalidateSize(), 100);
    }
}

// Map Functions
function initializeMap() {
    const mapContainer = document.getElementById('map');
    if (!mapContainer || currentMap) return;
    
    currentMap = L.map('map').setView([20.5937, 78.9629], 5);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(currentMap);
    
    addCityMarkers();
}

async function addCityMarkers() {
    if (!currentMap) return;
    
    try {
        const citiesResponse = await fetch(`${API_BASE_URL}/cities`);
        const cities = await citiesResponse.json();
        
        for (const city of cities) {
            const aqiResponse = await fetch(`${API_BASE_URL}/aqi/current/${city.name}`);
            const aqiData = await aqiResponse.json();
            
            const coords = await getCityCoordinates(city.name);
            if (!coords) continue;
            
            const aqi = aqiData.aqi || 0;
            const color = getAQIColor(aqi);
            
            const marker = L.circleMarker([coords.lat, coords.lon], {
                radius: 10,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(currentMap);
            
            marker.bindPopup(`
                <div style="text-align: center;">
                    <h3 style="margin: 0 0 10px 0;">${city.name}</h3>
                    <div style="font-size: 2em; font-weight: bold; color: ${color};">
                        ${aqi}
                    </div>
                    <div style="margin: 5px 0;">${getAQICategory(aqi)}</div>
                    <div style="font-size: 0.9em; color: #666;">
                        PM2.5: ${aqiData.pm25 || 'N/A'} μg/m³<br>
                        PM10: ${aqiData.pm10 || 'N/A'} μg/m³
                    </div>
                </div>
            `);
        }
    } catch (error) {
        console.error('Error adding city markers:', error);
    }
}

async function getCityCoordinates(cityName) {
    try {
        const response = await fetch(`${API_BASE_URL}/cities/coordinates/${cityName}`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error(`Error getting coordinates for ${cityName}:`, error);
    }
    return null;
}

// Trends Functions
async function loadHistoricalTrends() {
    const city = document.getElementById('trendsCity')?.value || 'Delhi';
    const days = document.getElementById('trendsPeriod')?.value || 7;
    
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/history/${city}?days=${days}`);
        const data = await response.json();
        
        if (!data || data.length === 0) {
            document.getElementById('trendsChart').innerHTML = 
                '<div class="no-data">No historical data available</div>';
            return;
        }
        
        // Plot AQI trend
        const aqiTrace = {
            x: data.map(d => d.timestamp),
            y: data.map(d => d.aqi),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'AQI',
            line: { color: '#667eea', width: 3 }
        };
        
        Plotly.newPlot('trendsChart', [aqiTrace], {
            title: `AQI Trend - ${city} (Last ${days} Days)`,
            xaxis: { title: 'Date' },
            yaxis: { title: 'AQI' },
            height: 400
        });
        
        // Plot pollutants
        const pm25Trace = {
            x: data.map(d => d.timestamp),
            y: data.map(d => d.pm25),
            type: 'scatter',
            mode: 'lines',
            name: 'PM2.5',
            line: { color: '#ff7e00' }
        };
        
        const pm10Trace = {
            x: data.map(d => d.timestamp),
            y: data.map(d => d.pm10),
            type: 'scatter',
            mode: 'lines',
            name: 'PM10',
            line: { color: '#00e400' }
        };
        
        Plotly.newPlot('pollutantsChart', [pm25Trace, pm10Trace], {
            title: 'Pollutant Levels',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Concentration (μg/m³)' },
            height: 400
        });
        
    } catch (error) {
        console.error('Error loading trends:', error);
        document.getElementById('trendsChart').innerHTML = 
            '<div class="error">Error loading trend data</div>';
    }
}

// Comparison Functions
function toggleCitySelection(cityName) {
    const index = selectedCities.indexOf(cityName);
    
    if (index > -1) {
        selectedCities.splice(index, 1);
    } else {
        if (selectedCities.length >= 6) {
            alert('Maximum 6 cities can be compared');
            return;
        }
        selectedCities.push(cityName);
    }
    
    // Update button states
    document.querySelectorAll('.city-selector').forEach(btn => {
        if (btn.textContent === cityName) {
            btn.classList.toggle('selected');
        }
    });
    
    loadComparison();
}

async function loadComparison() {
    const container = document.getElementById('comparisonResults');
    
    if (selectedCities.length === 0) {
        container.innerHTML = '<div class="no-data">Select cities to compare</div>';
        return;
    }
    
    try {
        const dataPromises = selectedCities.map(city => 
            fetch(`${API_BASE_URL}/aqi/current/${city}`).then(r => r.json())
        );
        
        const cityData = await Promise.all(dataPromises);
        
        // Display comparison cards
        container.innerHTML = `
            <div class="comparison-grid">
                ${cityData.map(data => `
                    <div class="city-card">
                        <h3>${data.city || 'Unknown'}</h3>
                        <div class="aqi-display ${getAQIColorClass(data.aqi)}">
                            ${data.aqi || 'N/A'}
                        </div>
                        <div style="margin-top: 15px;">
                            <div>PM2.5: ${data.pm25 || 'N/A'} μg/m³</div>
                            <div>PM10: ${data.pm10 || 'N/A'} μg/m³</div>
                            <div>CO: ${data.co || 'N/A'} ppm</div>
                            <div>NO₂: ${data.no2 || 'N/A'} ppb</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Create comparison chart
        const trace = {
            x: cityData.map(d => d.city),
            y: cityData.map(d => d.aqi),
            type: 'bar',
            marker: {
                color: cityData.map(d => getAQIColor(d.aqi))
            }
        };
        
        Plotly.newPlot('comparisonChart', [trace], {
            title: 'City AQI Comparison',
            xaxis: { title: 'City' },
            yaxis: { title: 'AQI' },
            height: 400
        });
        
    } catch (error) {
        console.error('Error loading comparison:', error);
        container.innerHTML = '<div class="error">Error loading comparison data</div>';
    }
}

// Alert Functions
async function createAlert(event) {
    event.preventDefault();
    
    const city = document.getElementById('alertCity').value;
    const email = document.getElementById('alertEmail').value;
    const threshold = parseInt(document.getElementById('alertThreshold').value);
    
    if (!city || !email || !threshold) {
        alert('Please fill all fields');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                city: city,
                alert_type: 'threshold',
                contact: email,
                threshold: threshold
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Alert created successfully!');
            document.getElementById('alertForm').reset();
            loadUserAlerts();
        } else {
            alert('Error creating alert: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error creating alert:', error);
        alert('Error creating alert. Please try again.');
    }
}

async function loadUserAlerts() {
    // For demo, load alerts for Delhi
    const city = 'Delhi';
    
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/list/${city}`);
        const alerts = await response.json();
        
        const container = document.getElementById('alertsList');
        
        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div class="no-data">No active alerts</div>';
            return;
        }
        
        container.innerHTML = `
            <ul class="alert-list">
                ${alerts.map(alert => `
                    <li class="alert-item">
                        <div>
                            <strong>${alert.city}</strong> - 
                            Threshold: ${alert.threshold} AQI
                            <br>
                            <small>Contact: ${alert.contact}</small>
                        </div>
                        <button class="btn btn-danger" onclick="deactivateAlert(${alert.id})">
                            Remove
                        </button>
                    </li>
                `).join('')}
            </ul>
        `;
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

async function deactivateAlert(alertId) {
    if (!confirm('Remove this alert?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/deactivate/${alertId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            alert('Alert removed');
            loadUserAlerts();
        } else {
            alert('Error removing alert');
        }
    } catch (error) {
        console.error('Error deactivating alert:', error);
        alert('Error removing alert');
    }
}

async function loadHealthRecommendations() {
    const city = 'Delhi'; // Default city
    
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/current/${city}`);
        const data = await response.json();
        
        const health = getHealthImpact(data.aqi);
        
        document.getElementById('healthInfo').innerHTML = `
            <div class="health-recommendation">
                <h3>${health.impact}</h3>
                <p><strong>Recommendations:</strong></p>
                <ul>
                    ${health.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
                <p><strong>At-Risk Groups:</strong> ${health.atRisk}</p>
            </div>
        `;
    } catch (error) {
        console.error('Error loading health recommendations:', error);
    }
}

function getHealthImpact(aqi) {
    if (aqi <= 50) {
        return {
            impact: 'Good - Air quality is satisfactory',
            recommendations: [
                'Ideal conditions for outdoor activities',
                'No health precautions needed'
            ],
            atRisk: 'None'
        };
    } else if (aqi <= 100) {
        return {
            impact: 'Moderate - Acceptable air quality',
            recommendations: [
                'Unusually sensitive people should limit prolonged outdoor exertion',
                'General population can enjoy outdoor activities'
            ],
            atRisk: 'Unusually sensitive individuals'
        };
    } else if (aqi <= 150) {
        return {
            impact: 'Unhealthy for Sensitive Groups',
            recommendations: [
                'Sensitive groups should reduce prolonged outdoor exertion',
                'Wear masks if going outside for extended periods',
                'Keep windows closed'
            ],
            atRisk: 'Children, elderly, people with respiratory/heart conditions'
        };
    } else if (aqi <= 200) {
        return {
            impact: 'Unhealthy - Everyone may experience health effects',
            recommendations: [
                'Limit outdoor activities',
                'Wear N95/N99 masks when going outside',
                'Use air purifiers indoors',
                'Avoid strenuous activities'
            ],
            atRisk: 'Everyone, especially sensitive groups'
        };
    } else if (aqi <= 300) {
        return {
            impact: 'Very Unhealthy - Health alert',
            recommendations: [
                'Avoid all outdoor activities',
                'Stay indoors with air purifiers',
                'Wear masks even for short outdoor exposure',
                'Seek medical attention if experiencing symptoms'
            ],
            atRisk: 'Everyone'
        };
    } else {
        return {
            impact: 'Hazardous - Health emergency',
            recommendations: [
                'STAY INDOORS',
                'Do not venture outside unless absolutely necessary',
                'Use N99 masks if must go out',
                'Run air purifiers continuously',
                'Seek immediate medical help if experiencing breathing difficulties'
            ],
            atRisk: 'Entire population at severe risk'
        };
    }
}

// ============================================================================
// FORECAST SECTION
// ============================================================================

async function loadDefaultCity() {
    const defaultCity = 'Delhi';
    document.getElementById('citySelect').value = defaultCity;
    await loadPredictions();
}

async function loadPredictions() {
    const city = document.getElementById('citySelect').value;
    
    if (!city) {
        alert('Please select a city');
        return;
    }
    
    try {
        // Load current AQI
        const currentResponse = await fetch(`${API_BASE_URL}/aqi/current/${city}`);
        currentData = await currentResponse.json();
        
        // Load prediction
        const predictionResponse = await fetch(`${API_BASE_URL}/aqi/forecast/${city}?hours=48`);
        predictionData = await predictionResponse.json();
        
        displayCurrentVsPredicted();
        displayPredictionChart();
        displayPollutants();
        displayHourlyForecast();
        displayModelMetrics();
        
    } catch (error) {
        console.error('Error loading predictions:', error);
        alert('Error loading predictions. Please try again.');
    }
}

function displayCurrentVsPredicted() {
    if (!currentData || !predictionData) return;
    
    const currentAQI = currentData.aqi || 0;
    const predictedAQI = predictionData.predicted_aqi || 0;
    const change = predictedAQI - currentAQI;
    
    document.getElementById('comparisonContainer').innerHTML = `
        <div class="comparison-grid">
            <div class="comparison-item current">
                <div class="label">Current AQI</div>
                <div class="value large ${getAQIColorClass(currentAQI)}">${currentAQI}</div>
                <div class="status">${getAQICategory(currentAQI)}</div>
                <div class="timestamp">${new Date(currentData.timestamp).toLocaleString()}</div>
            </div>
            
            <div class="comparison-arrow">→</div>
            
            <div class="comparison-item predicted">
                <div class="label">Predicted AQI (48h)</div>
                <div class="value large ${getAQIColorClass(predictedAQI)}">${predictedAQI}</div>
                <div class="status">${getAQICategory(predictedAQI)}</div>
                <div class="confidence">Confidence: ${predictionData.confidence || 'N/A'}%</div>
            </div>
        </div>
        
        <div class="change-indicator ${change > 0 ? 'aqi-unhealthy' : 'aqi-good'}">
            ${change > 0 ? '⬆' : '⬇'} ${Math.abs(change)} AQI points
        </div>
    `;
}

function displayPredictionChart() {
    if (!predictionData || !predictionData.forecast) return;
    
    const forecast = predictionData.forecast;
    
    const trace = {
        x: forecast.map(f => f.timestamp),
        y: forecast.map(f => f.aqi),
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Predicted AQI',
        line: { color: '#667eea', width: 3 }
    };
    
    Plotly.newPlot('predictionChart', [trace], {
        title: '48-Hour AQI Forecast',
        xaxis: { title: 'Time' },
        yaxis: { title: 'AQI' },
        height: 400
    });
}

function displayPollutants() {
    if (!predictionData) return;
    
    document.getElementById('pollutantsContainer').innerHTML = `
        <div class="pollutants-grid">
            <div class="pollutant-item">
                <span class="label">PM2.5</span>
                <span class="value">${predictionData.pm25 || 'N/A'}</span>
                <span class="unit">μg/m³</span>
            </div>
            <div class="pollutant-item">
                <span class="label">PM10</span>
                <span class="value">${predictionData.pm10 || 'N/A'}</span>
                <span class="unit">μg/m³</span>
            </div>
            <div class="pollutant-item">
                <span class="label">CO</span>
                <span class="value">${predictionData.co || 'N/A'}</span>
                <span class="unit">ppm</span>
            </div>
            <div class="pollutant-item">
                <span class="label">NO₂</span>
                <span class="value">${predictionData.no2 || 'N/A'}</span>
                <span class="unit">ppb</span>
            </div>
            <div class="pollutant-item">
                <span class="label">O₃</span>
                <span class="value">${predictionData.o3 || 'N/A'}</span>
                <span class="unit">ppb</span>
            </div>
            <div class="pollutant-item">
                <span class="label">SO₂</span>
                <span class="value">${predictionData.so2 || 'N/A'}</span>
                <span class="unit">ppb</span>
            </div>
        </div>
    `;
}

function displayHourlyForecast() {
    if (!predictionData || !predictionData.forecast) return;
    
    const tbody = document.getElementById('hourlyForecastTable');
    tbody.innerHTML = predictionData.forecast.map(hour => `
        <tr>
            <td>${new Date(hour.timestamp).toLocaleString()}</td>
            <td><strong>${hour.aqi}</strong></td>
            <td>${hour.pm25 || 'N/A'}</td>
            <td>${hour.pm10 || 'N/A'}</td>
            <td><span class="${getAQIColorClass(hour.aqi)}" style="padding: 5px 10px; border-radius: 5px;">
                ${getAQICategory(hour.aqi)}
            </span></td>
        </tr>
    `).join('');
}

function displayModelMetrics() {
    if (!predictionData || !predictionData.model_metrics) return;
    
    const metrics = predictionData.model_metrics;
    
    document.getElementById('metricsContainer').innerHTML = `
        <div class="metrics-grid">
            <div class="pollutant-item">
                <span class="label">Model Used</span>
                <span class="value" style="font-size: 1.2em;">${metrics.model_name || 'Ensemble'}</span>
            </div>
            <div class="pollutant-item">
                <span class="label">Accuracy</span>
                <span class="value">${metrics.accuracy || 'N/A'}</span>
                <span class="unit">%</span>
            </div>
            <div class="pollutant-item">
                <span class="label">MAE</span>
                <span class="value">${metrics.mae || 'N/A'}</span>
            </div>
            <div class="pollutant-item">
                <span class="label">RMSE</span>
                <span class="value">${metrics.rmse || 'N/A'}</span>
            </div>
        </div>
    `;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getAQIColor(aqi) {
    if (aqi <= 50) return '#00e400';
    if (aqi <= 100) return '#ffff00';
    if (aqi <= 150) return '#ff7e00';
    if (aqi <= 200) return '#ff0000';
    if (aqi <= 300) return '#8f3f97';
    return '#7e0023';
}

function getAQIColorClass(aqi) {
    if (aqi <= 50) return 'aqi-good';
    if (aqi <= 100) return 'aqi-moderate';
    if (aqi <= 150) return 'aqi-unhealthy-sensitive';
    if (aqi <= 200) return 'aqi-unhealthy';
    if (aqi <= 300) return 'aqi-very-unhealthy';
    return 'aqi-hazardous';
}

function getAQICategory(aqi) {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    if (aqi <= 200) return 'Unhealthy';
    if (aqi <= 300) return 'Very Unhealthy';
    return 'Hazardous';
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Show home section by default
    showSection('home');
    
    // Load cities for comparison selector
    loadCitiesForComparison();
    
    // Load cities for forecast selector
    loadCitiesForForecast();
});

async function loadCitiesForComparison() {
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        const cities = await response.json();
        
        const container = document.getElementById('citySelectorContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="selector-group">
                ${cities.slice(0, 20).map(city => `
                    <button class="city-selector" onclick="toggleCitySelection('${city.name}')">
                        ${city.name}
                    </button>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Error loading cities for comparison:', error);
    }
}

async function loadCitiesForForecast() {
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        const cities = await response.json();
        
        const select = document.getElementById('citySelect');
        if (!select) return;
        
        select.innerHTML = cities.map(city => `
            <option value="${city.name}">${city.name}</option>
        `).join('');
    } catch (error) {
        console.error('Error loading cities for forecast:', error);
    }
}
