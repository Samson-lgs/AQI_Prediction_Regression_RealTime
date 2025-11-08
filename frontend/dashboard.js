// Dashboard JavaScript for AQI Interactive Features
const API_BASE_URL = typeof config !== 'undefined' ? config.API_BASE_URL : 'http://localhost:5000/api/v1';

let map = null;
let markers = [];
let citiesData = [];
let selectedCities = [];
let userAlerts = [];

// Initialize app on load
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Initializing AQI Dashboard...');
    await loadCities();
    await initializeMap();
    await loadCityRankings();
    populateCitySelectors();
});

// ============================================================================
// TAB SWITCHING
// ============================================================================
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all nav tabs
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');
    
    // Load tab-specific data
    if (tabName === 'map' && map) {
        setTimeout(() => map.invalidateSize(), 100);
    } else if (tabName === 'trends') {
        loadHistoricalTrends();
    } else if (tabName === 'comparison') {
        loadComparison();
    } else if (tabName === 'alerts') {
        loadUserAlerts();
    }
}

// ============================================================================
// DATA LOADING
// ============================================================================
async function loadCities() {
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        if (!response.ok) throw new Error('Failed to fetch cities');
        
        const data = await response.json();
        citiesData = Array.isArray(data) ? data.map(c => c.name || c) : [];
        
        // Populate city dropdowns
        ['trendCity', 'alertCity', 'healthCity'].forEach(id => {
            const select = document.getElementById(id);
            select.innerHTML = '<option value="">Select a city...</option>';
            citiesData.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                select.appendChild(option);
            });
        });
        
        console.log(`Loaded ${citiesData.length} cities`);
        return citiesData;
    } catch (error) {
        console.error('Error loading cities:', error);
        return [];
    }
}

async function loadCityAQI(city) {
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/current/${city}`);
        if (!response.ok) return null;
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`Error loading AQI for ${city}:`, error);
        return null;
    }
}

// ============================================================================
// MAP FUNCTIONALITY
// ============================================================================
async function initializeMap() {
    // Initialize Leaflet map centered on India
    map = L.map('map').setView([20.5937, 78.9629], 5);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Load all cities and add markers
    await addCityMarkers();
}

async function addCityMarkers() {
    for (const city of citiesData) {
        const aqiData = await loadCityAQI(city);
        if (!aqiData) continue;
        
        const coords = await getCityCoordinates(city);
        if (!coords) continue;
        
        const aqi = aqiData.aqi || 0;
        const color = getAQIColor(aqi);
        const category = getAQICategory(aqi);
        
        // Create custom marker
        const marker = L.circleMarker([coords.lat, coords.lon], {
            radius: 12,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
        // Create popup
        const popupContent = `
            <div style="min-width: 200px;">
                <h3 style="margin: 0 0 10px 0; color: #667eea;">${city}</h3>
                <div style="background: ${color}; color: white; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                    <div style="font-size: 2em; font-weight: bold;">${Math.round(aqi)}</div>
                    <div>${category}</div>
                </div>
                <div style="font-size: 0.9em;">
                    <strong>PM2.5:</strong> ${aqiData.pm25?.toFixed(1) || 'N/A'} µg/m³<br>
                    <strong>PM10:</strong> ${aqiData.pm10?.toFixed(1) || 'N/A'} µg/m³<br>
                    <strong>Updated:</strong> ${new Date(aqiData.timestamp).toLocaleString()}
                </div>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        markers.push({ city, marker, aqi });
    }
    
    console.log(`Added ${markers.length} city markers to map`);
}

async function getCityCoordinates(city) {
    // Use backend to get coordinates
    try {
        const response = await fetch(`${API_BASE_URL}/cities/coordinates/${city}`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.warn(`Could not fetch coordinates for ${city}, using defaults`);
    }
    
    // Fallback coordinates for major cities
    const fallbackCoords = {
        'Delhi': { lat: 28.7041, lon: 77.1025 },
        'Mumbai': { lat: 19.0760, lon: 72.8777 },
        'Bangalore': { lat: 12.9716, lon: 77.5946 },
        'Chennai': { lat: 13.0827, lon: 80.2707 },
        'Kolkata': { lat: 22.5726, lon: 88.3639 },
        'Hyderabad': { lat: 17.3850, lon: 78.4867 },
        'Pune': { lat: 18.5204, lon: 73.8567 },
        'Ahmedabad': { lat: 23.0225, lon: 72.5714 }
    };
    
    return fallbackCoords[city] || null;
}

// ============================================================================
// CITY RANKINGS
// ============================================================================
async function loadCityRankings() {
    try {
        const allAQI = await Promise.all(
            citiesData.slice(0, 20).map(async city => {
                const data = await loadCityAQI(city);
                return data ? { city, aqi: data.aqi || 0 } : null;
            })
        );
        
        const validData = allAQI.filter(d => d !== null);
        validData.sort((a, b) => b.aqi - a.aqi);
        
        const cities = validData.map(d => d.city);
        const aqis = validData.map(d => d.aqi);
        const colors = aqis.map(aqi => getAQIColor(aqi));
        
        const trace = {
            x: aqis,
            y: cities,
            type: 'bar',
            orientation: 'h',
            marker: {
                color: colors
            },
            text: aqis.map(aqi => Math.round(aqi)),
            textposition: 'outside'
        };
        
        const layout = {
            title: 'Top 20 Cities by AQI (Highest to Lowest)',
            xaxis: { title: 'AQI Value' },
            yaxis: { autorange: 'reversed' },
            height: 600,
            margin: { l: 150 }
        };
        
        Plotly.newPlot('rankingsChart', [trace], layout, { responsive: true });
    } catch (error) {
        console.error('Error loading rankings:', error);
    }
}

// ============================================================================
// HISTORICAL TRENDS
// ============================================================================
async function loadHistoricalTrends() {
    const city = document.getElementById('trendCity').value;
    const days = document.getElementById('trendDays').value;
    
    if (!city) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/aqi/history/${city}?days=${days}`);
        if (!response.ok) throw new Error('Failed to fetch history');
        
        const historyData = await response.json();
        
        if (!historyData || historyData.length === 0) {
            document.getElementById('aqiTrendChart').innerHTML = '<p class="loading">No historical data available for this city</p>';
            return;
        }
        
        // Sort by timestamp
        historyData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        const timestamps = historyData.map(d => new Date(d.timestamp));
        const aqiValues = historyData.map(d => d.aqi || 0);
        const pm25Values = historyData.map(d => d.pm25 || 0);
        const pm10Values = historyData.map(d => d.pm10 || 0);
        
        // AQI Trend Chart
        const aqiTrace = {
            x: timestamps,
            y: aqiValues,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'AQI',
            line: { color: '#667eea', width: 3 },
            marker: { size: 6 }
        };
        
        const aqiLayout = {
            title: `AQI Trend for ${city} (Last ${days} Days)`,
            xaxis: { title: 'Date' },
            yaxis: { title: 'AQI Value' },
            height: 400
        };
        
        Plotly.newPlot('aqiTrendChart', [aqiTrace], aqiLayout, { responsive: true });
        
        // Pollutants Trend Chart
        const pm25Trace = {
            x: timestamps,
            y: pm25Values,
            type: 'scatter',
            mode: 'lines',
            name: 'PM2.5',
            line: { color: '#ff6b6b', width: 2 }
        };
        
        const pm10Trace = {
            x: timestamps,
            y: pm10Values,
            type: 'scatter',
            mode: 'lines',
            name: 'PM10',
            line: { color: '#4ecdc4', width: 2 }
        };
        
        const pollutantsLayout = {
            title: `Pollutant Concentrations for ${city}`,
            xaxis: { title: 'Date' },
            yaxis: { title: 'Concentration (µg/m³)' },
            height: 400
        };
        
        Plotly.newPlot('pollutantsTrendChart', [pm25Trace, pm10Trace], pollutantsLayout, { responsive: true });
        
    } catch (error) {
        console.error('Error loading historical trends:', error);
        document.getElementById('aqiTrendChart').innerHTML = `<p class="error">Error loading data: ${error.message}</p>`;
    }
}

// ============================================================================
// MULTI-CITY COMPARISON
// ============================================================================
function populateCitySelectors() {
    const container = document.getElementById('citySelectors');
    container.innerHTML = '';
    
    citiesData.slice(0, 30).forEach(city => {
        const btn = document.createElement('button');
        btn.className = 'city-selector';
        btn.textContent = city;
        btn.onclick = () => toggleCitySelection(city, btn);
        container.appendChild(btn);
    });
}

function toggleCitySelection(city, btn) {
    if (selectedCities.includes(city)) {
        selectedCities = selectedCities.filter(c => c !== city);
        btn.classList.remove('selected');
    } else {
        if (selectedCities.length >= 6) {
            alert('Maximum 6 cities can be compared at once');
            return;
        }
        selectedCities.push(city);
        btn.classList.add('selected');
    }
    
    loadComparison();
}

async function loadComparison() {
    if (selectedCities.length === 0) {
        document.getElementById('comparisonGrid').innerHTML = '<p class="loading">Select cities from above to compare</p>';
        return;
    }
    
    const grid = document.getElementById('comparisonGrid');
    grid.innerHTML = '';
    
    const comparisonData = await Promise.all(
        selectedCities.map(async city => {
            const data = await loadCityAQI(city);
            return { city, ...data };
        })
    );
    
    // Create city cards
    comparisonData.forEach(data => {
        if (!data) return;
        
        const aqi = data.aqi || 0;
        const category = getAQICategory(aqi);
        const color = getAQIColor(aqi);
        
        const card = document.createElement('div');
        card.className = 'city-card';
        card.innerHTML = `
            <div class="city-name">${data.city}</div>
            <div class="aqi-display" style="background: ${color}; ${aqi > 100 ? 'color: white;' : 'color: #333;'}">
                ${Math.round(aqi)}
            </div>
            <div style="text-align: center; font-weight: bold; margin-bottom: 10px;">${category}</div>
            <div class="pollutant-row">
                <span>PM2.5:</span>
                <strong>${data.pm25?.toFixed(1) || 'N/A'} µg/m³</strong>
            </div>
            <div class="pollutant-row">
                <span>PM10:</span>
                <strong>${data.pm10?.toFixed(1) || 'N/A'} µg/m³</strong>
            </div>
            <div class="pollutant-row">
                <span>NO₂:</span>
                <strong>${data.no2?.toFixed(1) || 'N/A'} µg/m³</strong>
            </div>
            <div class="pollutant-row">
                <span>SO₂:</span>
                <strong>${data.so2?.toFixed(1) || 'N/A'} µg/m³</strong>
            </div>
            <div style="margin-top: 10px; font-size: 0.85em; color: #666;">
                Updated: ${new Date(data.timestamp).toLocaleString()}
            </div>
        `;
        grid.appendChild(card);
    });
    
    // Create comparison chart
    const cities = comparisonData.map(d => d.city);
    const aqis = comparisonData.map(d => d.aqi || 0);
    const colors = aqis.map(aqi => getAQIColor(aqi));
    
    const trace = {
        x: cities,
        y: aqis,
        type: 'bar',
        marker: { color: colors },
        text: aqis.map(aqi => Math.round(aqi)),
        textposition: 'outside'
    };
    
    const layout = {
        title: 'AQI Comparison',
        yaxis: { title: 'AQI Value' },
        height: 400
    };
    
    Plotly.newPlot('comparisonChart', [trace], layout, { responsive: true });
}

// ============================================================================
// ALERTS MANAGEMENT
// ============================================================================
async function createAlert(event) {
    event.preventDefault();
    
    const city = document.getElementById('alertCity').value;
    const email = document.getElementById('alertEmail').value;
    const threshold = document.getElementById('alertThreshold').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                city: city,
                alert_type: 'email',
                contact: email,
                threshold: parseInt(threshold)
            })
        });
        
        if (!response.ok) throw new Error('Failed to create alert');
        
        alert('Alert created successfully! You will be notified when AQI exceeds your threshold.');
        document.getElementById('alertForm').reset();
        loadUserAlerts();
    } catch (error) {
        console.error('Error creating alert:', error);
        alert('Error creating alert: ' + error.message);
    }
}

async function loadUserAlerts() {
    // For demo purposes, we'll show alerts for a sample city
    // In production, this would filter by user session/email
    const city = citiesData[0] || 'Delhi';
    
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/list/${city}`);
        if (!response.ok) {
            document.getElementById('alertsList').innerHTML = '<li class="alert-item">No active alerts</li>';
            return;
        }
        
        const alerts = await response.json();
        const list = document.getElementById('alertsList');
        list.innerHTML = '';
        
        if (!alerts || alerts.length === 0) {
            list.innerHTML = '<li class="alert-item">No active alerts</li>';
            return;
        }
        
        alerts.forEach(alert => {
            const li = document.createElement('li');
            li.className = 'alert-item';
            li.innerHTML = `
                <div>
                    <strong>${alert.city}</strong> - Threshold: ${alert.threshold} AQI
                    <br><small>Email: ${alert.contact}</small>
                </div>
                <button class="btn btn-danger" onclick="deactivateAlert(${alert.id})">Remove</button>
            `;
            list.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

async function deactivateAlert(alertId) {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/deactivate/${alertId}`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to deactivate alert');
        
        alert('Alert removed successfully');
        loadUserAlerts();
    } catch (error) {
        console.error('Error deactivating alert:', error);
        alert('Error removing alert: ' + error.message);
    }
}

// ============================================================================
// HEALTH RECOMMENDATIONS
// ============================================================================
async function loadHealthRecommendations() {
    const city = document.getElementById('healthCity').value;
    if (!city) return;
    
    const aqiData = await loadCityAQI(city);
    if (!aqiData) {
        document.getElementById('healthContent').innerHTML = '<p class="error">Unable to load health recommendations</p>';
        return;
    }
    
    const aqi = aqiData.aqi || 0;
    const category = getAQICategory(aqi);
    const color = getAQIColor(aqi);
    const health = getHealthImpact(aqi);
    
    const content = `
        <div class="aqi-display" style="background: ${color}; ${aqi > 100 ? 'color: white;' : 'color: #333;'}">
            ${Math.round(aqi)}
            <div style="font-size: 0.4em; margin-top: 10px;">${category}</div>
        </div>
        
        <div class="health-recommendation">
            <h3>⚠️ Health Impact</h3>
            <p>${health.impact}</p>
            
            <h3 style="margin-top: 20px;">🏃 Activity Recommendations</h3>
            <ul>
                ${health.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
            
            <h3 style="margin-top: 20px;">👥 At-Risk Groups</h3>
            <p>${health.atRisk}</p>
        </div>
    `;
    
    document.getElementById('healthContent').innerHTML = content;
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

function getAQICategory(aqi) {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    if (aqi <= 200) return 'Unhealthy';
    if (aqi <= 300) return 'Very Unhealthy';
    return 'Hazardous';
}

function getHealthImpact(aqi) {
    if (aqi <= 50) {
        return {
            impact: 'Air quality is satisfactory, and air pollution poses little or no risk.',
            recommendations: [
                'Enjoy outdoor activities',
                'No restrictions on physical activities',
                'Windows can be kept open for ventilation'
            ],
            atRisk: 'None'
        };
    } else if (aqi <= 100) {
        return {
            impact: 'Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.',
            recommendations: [
                'Unusually sensitive people should consider limiting prolonged outdoor activities',
                'General population can enjoy normal outdoor activities',
                'Monitor symptoms if you have respiratory conditions'
            ],
            atRisk: 'Unusually sensitive individuals with respiratory conditions'
        };
    } else if (aqi <= 150) {
        return {
            impact: 'Members of sensitive groups may experience health effects. The general public is less likely to be affected.',
            recommendations: [
                'Sensitive groups should limit prolonged outdoor exertion',
                'Close windows to avoid dirty outdoor air',
                'Run an air purifier if available',
                'Wear N95 masks when outdoors'
            ],
            atRisk: 'Children, elderly, people with heart or lung disease, pregnant women'
        };
    } else if (aqi <= 200) {
        return {
            impact: 'Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.',
            recommendations: [
                'Everyone should avoid prolonged outdoor exertion',
                'Sensitive groups should avoid all outdoor physical activity',
                'Keep windows and doors closed',
                'Use air purifiers indoors',
                'Wear N95 masks if you must go outside'
            ],
            atRisk: 'Children, elderly, people with heart/lung disease, outdoor workers'
        };
    } else if (aqi <= 300) {
        return {
            impact: 'Health alert: The risk of health effects is increased for everyone.',
            recommendations: [
                'Everyone should avoid all outdoor exertion',
                'Stay indoors with windows closed',
                'Run air purifiers continuously',
                'Reschedule outdoor activities',
                'If you must go out, wear N95/N99 masks',
                'Avoid smoking and using candles/incense'
            ],
            atRisk: 'Everyone, especially children, elderly, and those with existing health conditions'
        };
    } else {
        return {
            impact: 'Health warning of emergency conditions: everyone is more likely to be affected.',
            recommendations: [
                'Everyone should avoid all outdoor activities',
                'Remain indoors with windows and doors sealed',
                'Use air purifiers on high settings',
                'Seek medical attention if experiencing symptoms',
                'Do not exercise indoors',
                'Avoid cooking that produces smoke or fumes'
            ],
            atRisk: 'Entire population - serious health effects for everyone'
        };
    }
}
