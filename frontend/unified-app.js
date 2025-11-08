/* ============================================================================
   UNIFIED AQI SYSTEM APPLICATION
   ============================================================================ */

// API Configuration
const API_BASE_URL = config?.API_BASE_URL || 'http://localhost:5000/api/v1';

// Global State
let currentMap = null;
let selectedCities = [];
let currentData = null;
let predictionData = null;
let citiesCache = null; // Cache cities to avoid repeated API calls
let citiesPromise = null; // Promise to handle concurrent requests
let fetchAttempts = 0; // Track fetch attempts

// Helper function to get cities (with caching, promise deduplication, and retry)
async function getCities() {
    // If we have cached data, return it immediately
    if (citiesCache) {
        return citiesCache;
    }
    
    // If a request is already in progress, wait for it
    if (citiesPromise) {
        return citiesPromise;
    }
    
    // Start a new request with retry logic
    citiesPromise = (async () => {
        let retries = 3;
        let delay = 1000; // Start with 1 second delay
        
        for (let i = 0; i < retries; i++) {
            try {
                // Add delay between retries
                if (i > 0) {
                    await new Promise(resolve => setTimeout(resolve, delay));
                    delay *= 2; // Exponential backoff
                }
                
                const response = await fetch(`${API_BASE_URL}/cities`);
                
                // If rate limited, try again
                if (response.status === 429) {
                    console.warn(`Rate limited (429), retry ${i + 1}/${retries}...`);
                    continue;
                }
                
                if (!response.ok) {
                    console.warn('Failed to load cities:', response.status);
                    if (i === retries - 1) {
                        citiesPromise = null;
                        return [];
                    }
                    continue;
                }
                
                const cities = await response.json();
                
                if (!Array.isArray(cities)) {
                    console.warn('Cities response is not an array:', cities);
                    citiesPromise = null;
                    return [];
                }
                
                citiesCache = cities;
                fetchAttempts = 0;
                return cities;
                
            } catch (error) {
                console.error(`Error fetching cities (attempt ${i + 1}/${retries}):`, error);
                if (i === retries - 1) {
                    citiesPromise = null;
                    return [];
                }
            }
        }
        
        citiesPromise = null;
        return [];
    })();
    
    return citiesPromise;
}

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
        const cities = await getCities();
        
        if (cities.length === 0) return;
        
        // Update total cities
        const totalCitiesEl = document.getElementById('totalCities');
        if (totalCitiesEl) totalCitiesEl.textContent = cities.length;
        
        // Get current AQI for a sample of cities (to avoid too many requests)
        const sampleCities = cities.slice(0, 10);
        const aqiPromises = sampleCities.map(city => 
            fetch(`${API_BASE_URL}/aqi/current/${city.name}`)
                .then(r => r.ok ? r.json() : null)
                .catch(() => null)
        );
        
        const allAqi = await Promise.all(aqiPromises);
        const validAqi = allAqi.filter(data => data && data.aqi);
        
        if (validAqi.length > 0) {
            const avgAqi = Math.round(
                validAqi.reduce((sum, data) => sum + data.aqi, 0) / validAqi.length
            );
            const avgAqiEl = document.getElementById('currentAvgAQI');
            if (avgAqiEl) avgAqiEl.textContent = avgAqi;
        }
        
        // Update data sources (hardcoded as per system design)
        const dataSourcesEl = document.getElementById('dataSources');
        if (dataSourcesEl) dataSourcesEl.textContent = '3';
        
        // Update active alerts (mock for now)
        const activeAlertsEl = document.getElementById('activeAlerts');
        if (activeAlertsEl) activeAlertsEl.textContent = '0';
        
    } catch (error) {
        console.error('Error loading home stats:', error);
    }
}

async function loadTopCities() {
    try {
        const cities = await getCities();
        
        if (cities.length === 0) return;
        
        // Get AQI for top 8 cities only (to avoid too many requests)
        const topCities = cities.slice(0, 8);
        const cityDataPromises = topCities.map(async city => {
            try {
                const aqiResponse = await fetch(`${API_BASE_URL}/aqi/current/${city.name}`);
                if (!aqiResponse.ok) return null;
                
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
        
        if (cityData.length === 0) {
            const grid = document.getElementById('topCitiesGrid');
            if (grid) grid.innerHTML = '<div class="no-data">Loading city data...</div>';
            return;
        }
        
        // Sort by AQI descending
        cityData.sort((a, b) => b.aqi - a.aqi);
        
        // Display in grid
        const grid = document.getElementById('topCitiesGrid');
        if (!grid) return;
        
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
        const grid = document.getElementById('topCitiesGrid');
        if (grid) {
            grid.innerHTML = '<div class="error">Unable to load city data</div>';
        }
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
        loadCityRankings();
        loadCitiesForTrends();
        loadCitiesForAlerts();
        loadCitiesForComparison();
    }
}

async function loadCityRankings() {
    try {
        const cities = await getCities();
        
        if (cities.length === 0) return;
        
        // Get AQI for top cities
        const cityPromises = cities.slice(0, 20).map(async (city) => {
            try {
                const aqiResponse = await fetch(`${API_BASE_URL}/aqi/current/${city.name}`);
                if (!aqiResponse.ok) return null;
                
                const aqiData = await aqiResponse.json();
                return {
                    city: city.name,
                    aqi: aqiData.aqi || 0
                };
            } catch {
                return null;
            }
        });
        
        const cityData = (await Promise.all(cityPromises)).filter(d => d !== null);
        cityData.sort((a, b) => b.aqi - a.aqi);
        
        const trace = {
            y: cityData.map(d => d.city),
            x: cityData.map(d => d.aqi),
            type: 'bar',
            orientation: 'h',
            marker: {
                color: cityData.map(d => getAQIColor(d.aqi))
            }
        };
        
        Plotly.newPlot('rankingsChart', [trace], {
            title: 'Top 20 Cities by AQI',
            xaxis: { title: 'AQI' },
            yaxis: { title: 'City' },
            height: 600,
            margin: { l: 100 }
        });
    } catch (error) {
        console.error('Error loading city rankings:', error);
    }
}

async function loadCitiesForTrends() {
    try {
        const cities = await getCities();
        
        const select = document.getElementById('trendCity');
        if (!select) return;
        
        select.innerHTML = cities.map(city => `
            <option value="${city.name}">${city.name}</option>
        `).join('');
        
        // Set default and load
        select.value = 'Delhi';
        loadHistoricalTrends();
    } catch (error) {
        console.error('Error loading cities for trends:', error);
    }
}

async function loadCitiesForAlerts() {
    try {
        const cities = await getCities();
        
        const select = document.getElementById('alertCity');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select a city...</option>' + cities.map(city => `
            <option value="${city.name}">${city.name}</option>
        `).join('');
    } catch (error) {
        console.error('Error loading cities for alerts:', error);
    }
}

function switchDashboardTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[onclick="switchDashboardTab('${tabName}')"]`)?.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.dashboard-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`dashboard-${tabName}`)?.classList.add('active');
    
    // Resize map if switching to map tab
    if (tabName === 'map' && currentMap) {
        setTimeout(() => currentMap.invalidateSize(), 100);
    }
    
    // Load data for specific tabs
    if (tabName === 'trends') {
        loadHistoricalTrends();
    } else if (tabName === 'comparison') {
        loadComparison();
    } else if (tabName === 'alerts') {
        loadUserAlerts();
        loadCitiesForHealth();
    } else if (tabName === 'map') {
        loadCityRankings();
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
    const citySelect = document.getElementById('trendCity');
    const daysSelect = document.getElementById('trendDays');
    
    const city = citySelect?.value || 'Delhi';
    const days = daysSelect?.value || 30;
    
    if (!city) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/history/${city}?days=${days}`);
        const data = await response.json();
        
        if (!data || data.length === 0) {
            const aqiChart = document.getElementById('aqiTrendChart');
            if (aqiChart) {
                aqiChart.innerHTML = '<div class="no-data">No historical data available</div>';
            }
            return;
        }
        
        // Plot AQI trend
        const aqiTrace = {
            x: data.map(d => d.timestamp),
            y: data.map(d => d.aqi),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'AQI',
            line: { color: '#667eea', width: 3 },
            marker: { size: 6 }
        };
        
        Plotly.newPlot('aqiTrendChart', [aqiTrace], {
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
            line: { color: '#ff7e00', width: 2 }
        };
        
        const pm10Trace = {
            x: data.map(d => d.timestamp),
            y: data.map(d => d.pm10),
            type: 'scatter',
            mode: 'lines',
            name: 'PM10',
            line: { color: '#00e400', width: 2 }
        };
        
        Plotly.newPlot('pollutantsTrendChart', [pm25Trace, pm10Trace], {
            title: 'Pollutant Levels',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Concentration (μg/m³)' },
            height: 400
        });
        
    } catch (error) {
        console.error('Error loading trends:', error);
        const aqiChart = document.getElementById('aqiTrendChart');
        if (aqiChart) {
            aqiChart.innerHTML = '<div class="error">Error loading trend data</div>';
        }
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
    const container = document.getElementById('comparisonGrid');
    
    if (!container) return;
    
    if (selectedCities.length === 0) {
        container.innerHTML = '<div class="no-data">Select cities above to compare (up to 6 cities)</div>';
        return;
    }
    
    try {
        const dataPromises = selectedCities.map(city => 
            fetch(`${API_BASE_URL}/aqi/current/${city}`).then(r => r.json())
        );
        
        const cityData = await Promise.all(dataPromises);
        
        // Display comparison cards
        container.innerHTML = cityData.map(data => `
            <div class="city-card">
                <h3>${data.city || 'Unknown'}</h3>
                <div class="aqi-display ${getAQIColorClass(data.aqi)}">
                    ${data.aqi || 'N/A'}
                </div>
                <div style="margin-top: 15px; font-size: 0.9em;">
                    <div><strong>PM2.5:</strong> ${data.pm25 || 'N/A'} μg/m³</div>
                    <div><strong>PM10:</strong> ${data.pm10 || 'N/A'} μg/m³</div>
                    <div><strong>CO:</strong> ${data.co || 'N/A'} ppm</div>
                    <div><strong>NO₂:</strong> ${data.no2 || 'N/A'} ppb</div>
                </div>
            </div>
        `).join('');
        
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
    const citySelect = document.getElementById('healthCity');
    const city = citySelect?.value || 'Delhi';
    
    if (!city) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/current/${city}`);
        const data = await response.json();
        
        const health = getHealthImpact(data.aqi);
        
        const healthContainer = document.getElementById('healthInfo');
        if (!healthContainer) return;
        
        healthContainer.innerHTML = `
            <div class="health-recommendation" style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 25px; border-radius: 12px;">
                <h3 style="color: #d63031; margin-bottom: 15px;">${health.impact}</h3>
                <p style="margin-bottom: 10px;"><strong>Current AQI in ${city}:</strong> ${data.aqi}</p>
                <p style="margin-bottom: 10px;"><strong>Recommendations:</strong></p>
                <ul style="margin: 10px 0 10px 20px;">
                    ${health.recommendations.map(rec => `<li style="margin-bottom: 8px;">${rec}</li>`).join('')}
                </ul>
                <p style="margin-top: 15px;"><strong>At-Risk Groups:</strong> ${health.atRisk}</p>
            </div>
        `;
    } catch (error) {
        console.error('Error loading health recommendations:', error);
        const healthContainer = document.getElementById('healthInfo');
        if (healthContainer) {
            healthContainer.innerHTML = '<div class="error">Error loading health recommendations</div>';
        }
    }
}

async function loadCitiesForHealth() {
    try {
        const cities = await getCities();
        
        const select = document.getElementById('healthCity');
        if (!select) return;
        
        select.innerHTML = cities.map(city => `
            <option value="${city.name}">${city.name}</option>
        `).join('');
        
        // Set default and load
        select.value = 'Delhi';
        loadHealthRecommendations();
    } catch (error) {
        console.error('Error loading cities for health:', error);
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
    const citySelect = document.getElementById('forecastCity');
    if (citySelect) {
        citySelect.value = defaultCity;
        await loadForecast();
    }
}

// Alias for button onclick
async function loadForecast() {
    await loadPredictions();
}

async function loadPredictions() {
    const city = document.getElementById('forecastCity')?.value;
    
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
    
    // Update current values
    const currentAqiValue = document.getElementById('currentAqiValue');
    const currentAqiStatus = document.getElementById('currentAqiStatus');
    const currentTimestamp = document.getElementById('currentTimestamp');
    
    if (currentAqiValue) currentAqiValue.textContent = currentAQI;
    if (currentAqiValue) currentAqiValue.className = `value large ${getAQIColorClass(currentAQI)}`;
    if (currentAqiStatus) currentAqiStatus.textContent = getAQICategory(currentAQI);
    if (currentTimestamp) currentTimestamp.textContent = new Date(currentData.timestamp).toLocaleString();
    
    // Update predicted values
    const predictedAqiValue = document.getElementById('predictedAqiValue');
    const predictedAqiStatus = document.getElementById('predictedAqiStatus');
    const confidenceValue = document.getElementById('confidenceValue');
    
    if (predictedAqiValue) predictedAqiValue.textContent = predictedAQI;
    if (predictedAqiValue) predictedAqiValue.className = `value large ${getAQIColorClass(predictedAQI)}`;
    if (predictedAqiStatus) predictedAqiStatus.textContent = getAQICategory(predictedAQI);
    if (confidenceValue) confidenceValue.textContent = predictionData.confidence || 'N/A';
    
    // Update change indicator
    const aqiChange = document.getElementById('aqiChange');
    if (aqiChange) {
        aqiChange.textContent = `${change > 0 ? '⬆' : '⬇'} ${Math.abs(change)} AQI points`;
        aqiChange.className = `change-indicator ${change > 0 ? 'aqi-unhealthy' : 'aqi-good'}`;
    }
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
    
    Plotly.newPlot('forecastChart', [trace], {
        title: '48-Hour AQI Forecast',
        xaxis: { title: 'Time' },
        yaxis: { title: 'AQI' },
        height: 400
    });
}

function displayPollutants() {
    if (!currentData) return;
    
    // Update individual pollutant values
    const pm25Value = document.getElementById('pm25Value');
    const pm10Value = document.getElementById('pm10Value');
    const no2Value = document.getElementById('no2Value');
    const so2Value = document.getElementById('so2Value');
    const coValue = document.getElementById('coValue');
    const o3Value = document.getElementById('o3Value');
    
    if (pm25Value) pm25Value.textContent = currentData.pm25 || 'N/A';
    if (pm10Value) pm10Value.textContent = currentData.pm10 || 'N/A';
    if (no2Value) no2Value.textContent = currentData.no2 || 'N/A';
    if (so2Value) so2Value.textContent = currentData.so2 || 'N/A';
    if (coValue) coValue.textContent = currentData.co || 'N/A';
    if (o3Value) o3Value.textContent = currentData.o3 || 'N/A';
}

function displayHourlyForecast() {
    if (!predictionData || !predictionData.forecast) return;
    
    const tbody = document.getElementById('hourlyTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = predictionData.forecast.slice(0, 24).map((hour, index) => {
        const prevAqi = index > 0 ? predictionData.forecast[index - 1].aqi : currentData?.aqi || 0;
        const change = hour.aqi - prevAqi;
        return `
            <tr>
                <td>${new Date(hour.timestamp).toLocaleString()}</td>
                <td><strong>${hour.aqi}</strong></td>
                <td><span class="${getAQIColorClass(hour.aqi)}" style="padding: 5px 10px; border-radius: 5px;">
                    ${getAQICategory(hour.aqi)}
                </span></td>
                <td style="color: ${change > 0 ? 'red' : 'green'};">
                    ${change > 0 ? '▲' : '▼'} ${Math.abs(change)}
                </td>
            </tr>
        `;
    }).join('');
}

function displayModelMetrics() {
    // Model metrics display removed as not in current HTML
    // Can be added later if needed
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

document.addEventListener('DOMContentLoaded', async () => {
    // Pre-load cities cache to avoid multiple simultaneous requests
    await getCities();
    
    // Show home section by default
    showSection('home');
    
    // Load cities for comparison selector (with small delay)
    setTimeout(() => loadCitiesForComparison(), 100);
    
    // Load cities for forecast selector (with small delay)
    setTimeout(() => loadCitiesForForecast(), 200);
});

async function loadCitiesForComparison() {
    try {
        const cities = await getCities();
        
        const container = document.getElementById('citySelectors');
        if (!container) return;
        
        container.innerHTML = cities.slice(0, 20).map(city => `
            <button class="city-selector" onclick="toggleCitySelection('${city.name}')">
                ${city.name}
            </button>
        `).join('');
    } catch (error) {
        console.error('Error loading cities for comparison:', error);
    }
}

async function loadCitiesForForecast() {
    try {
        const cities = await getCities();
        
        const select = document.getElementById('forecastCity');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select a city...</option>' + cities.map(city => `
            <option value="${city.name}">${city.name}</option>
        `).join('');
    } catch (error) {
        console.error('Error loading cities for forecast:', error);
    }
}
