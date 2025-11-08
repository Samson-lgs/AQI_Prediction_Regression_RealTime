/* ============================================================================
   UNIFIED AQI SYSTEM APPLICATION
   ============================================================================ */

// API Configuration

const API_BASE_URL = config?.API_BASE_URL || 'http://localhost:5000/api/v1';

// Global State
let currentMap = null;
let currentData = null;
let predictionData = null;
let citiesCache = null; // Cache cities to avoid repeated API calls
let citiesPromise = null; // Promise to handle concurrent requests
let fetchAttempts = 0; // Track fetch attempts
let selectedCities = []; // Cities chosen for comparison

// Add AQI standard badge on page load
document.addEventListener('DOMContentLoaded', () => {
    if (config?.SHOW_AQI_STANDARD && config?.AQI_STANDARD) {
        const badge = document.createElement('div');
        badge.id = 'aqiStandardBadge';
        badge.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        badge.innerHTML = `
            <span style="font-size: 1.2em;">🇮🇳</span>
            <span>AQI Standard: ${config.AQI_STANDARD}</span>
        `;
        document.body.appendChild(badge);
    }
});

const container = document.getElementById('alertsList');
if (container) {
    container.innerHTML = '<div class="no-data">Error loading alerts</div>';
}
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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        const data = result.data || result; // Handle both {data: [...]} and direct array formats
        
        if (!data || !Array.isArray(data) || data.length === 0) {
            const aqiChart = document.getElementById('aqiTrendChart');
            if (aqiChart) {
                aqiChart.innerHTML = '<div class="no-data">No historical data available for this city</div>';
            }
            return;
        }
        
        // Plot AQI trend
        const aqiTrace = {
            x: data.map(d => d.timestamp),
            y: data.map(d => d.aqi_value || d.aqi),
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
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const alerts = await response.json();
        
        const container = document.getElementById('alertsList');
        
        if (!alerts || !Array.isArray(alerts) || alerts.length === 0) {
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
        const container = document.getElementById('alertsList');
        if (container) {
            container.innerHTML = '<div class="no-data">Error loading alerts</div>';
        }
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
        
        const healthContainer = document.getElementById('healthContent');
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
        const healthContainer = document.getElementById('healthContent');
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
        // Show loading indicators
        const currentAqiValue = document.getElementById('currentAqiValue');
        const predictedAqiValue = document.getElementById('predictedAqiValue');
        if (currentAqiValue) currentAqiValue.textContent = 'Loading...';
        if (predictedAqiValue) predictedAqiValue.textContent = 'Loading...';
        
        // Load current AQI
        const currentResponse = await fetch(`${API_BASE_URL}/aqi/current/${city}`);
        
        if (!currentResponse.ok) {
            throw new Error(`Failed to load current AQI: ${currentResponse.status} ${currentResponse.statusText}`);
        }
        
        currentData = await currentResponse.json();
        
        // Load prediction
        // Corrected to /forecast/ namespace (previously /aqi/forecast/ caused 404)
        const predictionResponse = await fetch(`${API_BASE_URL}/forecast/${city}?hours=48`);
        
        if (!predictionResponse.ok) {
            throw new Error(`Failed to load forecast: ${predictionResponse.status} ${predictionResponse.statusText}`);
        }
        
        predictionData = await predictionResponse.json();

        // Normalize backend forecast response structure so downstream UI code works
        // Backend returns: { city, model_used, forecast_hours, predictions: [ {hour, forecast_timestamp, predicted_aqi, confidence} ] }
        // Existing UI expects: predictionData.predicted_aqi (single value) and predictionData.forecast = [{timestamp, aqi, confidence}]
        if (predictionData && Array.isArray(predictionData.predictions)) {
            // Map predictions to expected 'forecast' array with unified keys
            predictionData.forecast = predictionData.predictions.map(p => ({
                hour: p.hour,
                timestamp: p.forecast_timestamp,
                aqi: p.predicted_aqi,
                confidence: p.confidence
            }));

            // Choose a representative predicted AQI value for the comparison card:
            // Use the prediction at the selected forecast horizon (default last hour requested) or first if unavailable.
            const horizonIndex = Math.min((predictionData.forecast_hours || predictionData.forecast.length) - 1, predictionData.forecast.length - 1);
            if (horizonIndex >= 0) {
                predictionData.predicted_aqi = predictionData.forecast[horizonIndex].aqi;
                predictionData.confidence = predictionData.forecast[horizonIndex].confidence;
            } else {
                predictionData.predicted_aqi = 0;
            }
        } else {
            // Fallback to avoid runtime errors
            predictionData.forecast = [];
            if (typeof predictionData.predicted_aqi === 'undefined') {
                predictionData.predicted_aqi = 0;
            }
        }
        
    // Display all prediction components
    displayCurrentVsPredicted();
    displayPredictionChart();
    displayPollutants();
    displayHourlyForecast();
    displayModelMetrics(city);
        
    } catch (error) {
        console.error('Error loading predictions:', error);
        
        // Show user-friendly error message
        const currentAqiValue = document.getElementById('currentAqiValue');
        const predictedAqiValue = document.getElementById('predictedAqiValue');
        if (currentAqiValue) currentAqiValue.textContent = 'Error';
        if (predictedAqiValue) predictedAqiValue.textContent = 'Error';
        
        alert(`Error loading predictions for ${city}:\n${error.message}\n\nPlease try again or select a different city.`);
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
    if (currentAqiStatus) {
        let statusText = getAQICategory(currentAQI);
        // Add dominant pollutant if available
        if (currentData.dominant_pollutant) {
            statusText += ` (Primary: ${currentData.dominant_pollutant})`;
        }
        currentAqiStatus.textContent = statusText;
    }
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
    
    // Handle both old format (flat pollutants) and new format (nested pollutants object)
    const pollutants = currentData.pollutants || currentData;
    
    // Update individual pollutant values
    const pm25Value = document.getElementById('pm25Value');
    const pm10Value = document.getElementById('pm10Value');
    const no2Value = document.getElementById('no2Value');
    const so2Value = document.getElementById('so2Value');
    const coValue = document.getElementById('coValue');
    const o3Value = document.getElementById('o3Value');
    
    // Display pollutant concentrations
    if (pm25Value) pm25Value.textContent = pollutants.pm25 ? pollutants.pm25.toFixed(2) : 'N/A';
    if (pm10Value) pm10Value.textContent = pollutants.pm10 ? pollutants.pm10.toFixed(2) : 'N/A';
    if (no2Value) no2Value.textContent = pollutants.no2 ? pollutants.no2.toFixed(2) : 'N/A';
    if (so2Value) so2Value.textContent = pollutants.so2 ? pollutants.so2.toFixed(2) : 'N/A';
    if (coValue) coValue.textContent = pollutants.co ? pollutants.co.toFixed(3) : 'N/A';
    if (o3Value) o3Value.textContent = pollutants.o3 ? pollutants.o3.toFixed(2) : 'N/A';
    
    // Add sub-indices if available (shows AQI contribution of each pollutant)
    if (currentData.sub_indices) {
        const subIndices = currentData.sub_indices;
        const dominantPollutant = currentData.dominant_pollutant;
        
        // Add sub-index badges to pollutant cards
        const addSubIndexBadge = (elementId, pollutantKey, subIndexValue) => {
            const element = document.getElementById(elementId);
            if (!element) return;
            
            const parent = element.closest('.pollutant-card') || element.parentElement;
            if (!parent) return;
            
            // Remove existing badge if any
            const existingBadge = parent.querySelector('.sub-index-badge');
            if (existingBadge) existingBadge.remove();
            
            // Create new badge
            const badge = document.createElement('div');
            badge.className = 'sub-index-badge';
            badge.style.cssText = 'margin-top: 8px; padding: 4px 8px; border-radius: 6px; font-size: 0.85em; text-align: center;';
            
            if (subIndexValue) {
                const isDominant = dominantPollutant && pollutantKey === dominantPollutant;
                badge.style.background = isDominant ? '#fee2e2' : '#f3f4f6';
                badge.style.color = isDominant ? '#dc2626' : '#6b7280';
                badge.style.fontWeight = isDominant ? 'bold' : 'normal';
                badge.textContent = `Sub-Index: ${subIndexValue}${isDominant ? ' ⚠️' : ''}`;
            } else {
                badge.style.background = '#f9fafb';
                badge.style.color = '#9ca3af';
                badge.textContent = 'Sub-Index: N/A';
            }
            
            parent.appendChild(badge);
        };
        
        addSubIndexBadge('pm25Value', 'PM2.5', subIndices['PM2.5']);
        addSubIndexBadge('pm10Value', 'PM10', subIndices['PM10']);
        addSubIndexBadge('no2Value', 'NO2', subIndices['NO2']);
        addSubIndexBadge('so2Value', 'SO2', subIndices['SO2']);
        addSubIndexBadge('coValue', 'CO', subIndices['CO']);
        addSubIndexBadge('o3Value', 'O3', subIndices['O3']);
    }
    
    // Add data source and comparison info at the bottom
    const pollutantsSection = document.querySelector('.pollutants-grid') || document.getElementById('pollutantsContainer');
    if (pollutantsSection && currentData.data_source) {
        let sourceInfo = pollutantsSection.querySelector('.source-info');
        if (!sourceInfo) {
            sourceInfo = document.createElement('div');
            sourceInfo.className = 'source-info';
            sourceInfo.style.cssText = 'margin-top: 20px; padding: 12px; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 6px; font-size: 0.9em;';
            pollutantsSection.appendChild(sourceInfo);
        }
        
        let sourceText = `<strong>Data Source:</strong> ${currentData.data_source}`;
        
        if (currentData.sources_compared && currentData.sources_compared.length > 1) {
            const comparisonText = currentData.sources_compared
                .map(s => `${s.source}: ${s.aqi}`)
                .join(', ');
            sourceText += `<br><small style="color: #6b7280;">Sources compared: ${comparisonText} (showing highest)</small>`;
        }
        
        if (currentData.note) {
            sourceText += `<br><small style="color: #6b7280; font-style: italic;">${currentData.note}</small>`;
        }
        
        sourceInfo.innerHTML = sourceText;
    }
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

async function displayModelMetrics(city) {
    const container = document.getElementById('metricsContainer');
    const activeModelEl = document.getElementById('activeModel');
    if (!container) return;

    // Show loading state
    container.innerHTML = '<div class="loading">Loading model performance...</div>';

    try {
        // First get the actual model being used for predictions
        const forecastResp = await fetch(`${API_BASE_URL}/forecast/${city}?hours=1`);
        let actualModel = null;
        if (forecastResp.ok) {
            const forecastData = await forecastResp.json();
            actualModel = forecastData.model_used;
        }

        // Fetch comparison info (determines best model)
        const compareResp = await fetch(`${API_BASE_URL}/models/compare?city=${city}`);
        let compareData = null;
        if (compareResp.ok) {
            compareData = await compareResp.json();
        }

        const bestModel = actualModel || compareData?.best_model || null;
        const bestR2 = typeof compareData?.best_r2_score === 'number' ? compareData.best_r2_score : null;

        if (activeModelEl) {
            activeModelEl.textContent = bestModel ? bestModel.replace(/_/g, ' ').toUpperCase() : 'N/A';
            // Add/update a small badge with best R² next to Active Model
            const selector = document.querySelector('.model-selector');
            if (selector) {
                let r2Badge = document.getElementById('bestR2Badge');
                if (!r2Badge) {
                    r2Badge = document.createElement('span');
                    r2Badge.id = 'bestR2Badge';
                    r2Badge.style.marginLeft = '10px';
                    r2Badge.style.fontSize = '0.9em';
                    r2Badge.style.padding = '4px 8px';
                    r2Badge.style.borderRadius = '6px';
                    r2Badge.style.background = '#eef2ff';
                    r2Badge.style.color = '#374151';
                    selector.appendChild(r2Badge);
                }
                r2Badge.textContent = bestR2 !== null ? `R²: ${bestR2.toFixed(3)}` : 'R²: --';
            }
        }

        if (!bestModel) {
            container.innerHTML = '<p class="no-data">No model performance data available yet. Train models to see metrics.</p>';
            return;
        }

        // Fetch performance for ONLY the active model
        const perfResp = await fetch(`${API_BASE_URL}/models/performance/${city}?model=${bestModel}&days=30`);
        let perfData = null;
        if (perfResp.ok) {
            perfData = await perfResp.json();
        }

        // Get metrics for the active model
        const comparison = compareData?.comparison || {};
        const activeMetrics = comparison[bestModel] || perfData?.metrics?.[0] || {};

        if (!activeMetrics || Object.keys(activeMetrics).length === 0) {
            container.innerHTML = `<p class="no-data">No performance data available for ${bestModel}. Train the model to see metrics.</p>`;
            return;
        }

        // Build single card for active model only
        const m = {
            model_name: bestModel,
            r2_score: activeMetrics.r2_score ?? null,
            rmse: activeMetrics.rmse ?? null,
            mae: activeMetrics.mae ?? null,
            mape: activeMetrics.mape ?? null,
            last_updated: activeMetrics.last_updated ?? null
        };

        const cardsHtml = (() => {
            const isBest = true; // Always true since we're only showing the active model
            const displayName = m.model_name ? m.model_name.replace(/_/g, ' ').toUpperCase() : 'UNKNOWN MODEL';
            const r2 = m.r2_score !== null && m.r2_score !== undefined ? m.r2_score.toFixed(3) : '--';
            const rmse = m.rmse !== null && m.rmse !== undefined ? m.rmse.toFixed(2) : '--';
            const mae = m.mae !== null && m.mae !== undefined ? m.mae.toFixed(2) : '--';
            const mape = m.mape !== null && m.mape !== undefined ? m.mape.toFixed(2) + '%' : '--';
            
            // Detect suspiciously perfect metrics (likely overfitting or insufficient data)
            const isPerfect = m.r2_score >= 0.999 && m.rmse <= 0.01 && m.mae <= 0.01;
            const warningHtml = isPerfect ? `
                <div class="metric-warning" style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 12px 0; border-radius: 6px;">
                    <strong>⚠️ Warning: Suspiciously Perfect Metrics</strong>
                    <p style="margin: 4px 0 0 0; font-size: 0.9em; color: #92400e;">
                        R² = 1.0 usually indicates overfitting or insufficient training data. 
                        The model may not generalize well to new data. 
                        <strong>Collect more data (weeks/months)</strong> for reliable predictions.
                    </p>
                </div>
            ` : '';
            
            return `
                <div class="metric-card best-model-card">
                    <div class="metric-header">
                        <span class="model-name">${displayName} ⭐</span>
                        ${m.last_updated ? `<span class="metric-updated">${m.last_updated}</span>` : ''}
                    </div>
                    ${warningHtml}
                    <div class="metric-grid">
                        <div class="metric-item">
                            <span class="metric-label">R²</span>
                            <span class="metric-value">${r2}</span>
                            <span class="metric-hint">Explained variance</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">RMSE</span>
                            <span class="metric-value">${rmse}</span>
                            <span class="metric-hint">Avg error magnitude</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">MAE</span>
                            <span class="metric-value">${mae}</span>
                            <span class="metric-hint">Mean abs error</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">MAPE</span>
                            <span class="metric-value">${mape}</span>
                            <span class="metric-hint">Percent error</span>
                        </div>
                    </div>
                </div>
            `;
        })();

        // Add legend/explanation
        const legend = `
            <div class="metrics-legend">
                <p><strong>Active Model Performance:</strong> R² closer to 1 is better; RMSE/MAE lower is better; MAPE lower % is better.</p>
            </div>
        `;

        container.innerHTML = legend + cardsHtml;

        // Hide charts since we're only showing one model
        const r2Chart = document.getElementById('modelR2Chart');
        const errorChart = document.getElementById('modelErrorChart');
        if (r2Chart) r2Chart.style.display = 'none';
        if (errorChart) errorChart.style.display = 'none';

    } catch (err) {
        console.error('Error loading model metrics:', err);
        container.innerHTML = '<div class="error">Failed to load model metrics.</div>';
    }
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

// Expose functions for inline handlers defined in HTML
window.showSection = showSection;
window.switchDashboardTab = switchDashboardTab;
window.loadForecast = loadForecast;
window.toggleCitySelection = toggleCitySelection;
window.createAlert = createAlert;
window.deactivateAlert = deactivateAlert;
window.loadHistoricalTrends = loadHistoricalTrends;
window.loadUserAlerts = loadUserAlerts;
window.loadHealthRecommendations = loadHealthRecommendations;

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
