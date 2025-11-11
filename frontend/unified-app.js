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
let liveInitialized = false; // Prevent heavy re-inits on Live section

// Batch endpoint support flag to avoid repeated 404s
// null = unknown, true = available, false = not available (skip calling)
let BATCH_SUPPORTED = null;

// Global cooldown timestamp (ms since epoch) set when we hit 429 to pause further requests
let RATE_LIMITED_UNTIL = 0;

// AQI fetch cache to reduce repeated network calls
const AQI_CACHE_TTL_MS = 120000; // 2 minutes
const currentAQICache = new Map(); // key: city name, value: { data, ts }

// Static fallback coordinates for all 97 Indian cities (used if /cities endpoint lacks lat/lon)
// Coordinates approximate city centers
const CITY_COORDS = {
    // North India
    "Delhi": { lat: 28.7041, lon: 77.1025 },
    "Noida": { lat: 28.5921, lon: 77.1845 },
    "Ghaziabad": { lat: 28.6692, lon: 77.4538 },
    "Gurugram": { lat: 28.4595, lon: 77.0266 },
    "Gurgaon": { lat: 28.4595, lon: 77.0266 },
    "Faridabad": { lat: 28.4089, lon: 77.3178 },
    "Greater Noida": { lat: 28.4744, lon: 77.5040 },
    "Chandigarh": { lat: 30.7333, lon: 76.7794 },
    "Jaipur": { lat: 26.9124, lon: 75.7873 },
    "Lucknow": { lat: 26.8467, lon: 80.9462 },
    "Kanpur": { lat: 26.4499, lon: 80.3319 },
    "Varanasi": { lat: 25.3176, lon: 82.9739 },
    "Agra": { lat: 27.1767, lon: 78.0081 },
    "Amritsar": { lat: 31.6340, lon: 74.8723 },
    "Ludhiana": { lat: 30.9010, lon: 75.8573 },
    "Kota": { lat: 25.2138, lon: 75.8648 },
    "Jodhpur": { lat: 26.2389, lon: 73.0243 },
    "Udaipur": { lat: 24.5854, lon: 73.7125 },
    "Meerut": { lat: 28.9845, lon: 77.7064 },
    "Aligarh": { lat: 27.8974, lon: 78.0880 },
    "Allahabad": { lat: 25.4358, lon: 81.8463 },
    "Jalandhar": { lat: 31.3260, lon: 75.5762 },
    "Bareilly": { lat: 28.3670, lon: 79.4304 },
    "Moradabad": { lat: 28.8389, lon: 78.7765 },
    "Sonipat": { lat: 28.9931, lon: 77.0151 },
    "Panipat": { lat: 29.3909, lon: 76.9635 },
    "Alwar": { lat: 27.5530, lon: 76.6346 },
    "Bharatpur": { lat: 27.2152, lon: 77.4883 },
    "Mathura": { lat: 27.4924, lon: 77.6737 },
    "Rohtak": { lat: 28.8955, lon: 76.5893 },
    "Rewari": { lat: 28.1990, lon: 76.6189 },
    "Bhiwani": { lat: 28.7930, lon: 76.1395 },
    "Bhiwadi": { lat: 28.2091, lon: 76.8633 },
    "Srinagar": { lat: 34.0837, lon: 74.7973 },
    // South India
    "Bangalore": { lat: 12.9716, lon: 77.5946 },
    "Bengaluru": { lat: 12.9716, lon: 77.5946 },
    "Chennai": { lat: 13.0827, lon: 80.2707 },
    "Hyderabad": { lat: 17.3850, lon: 78.4867 },
    "Kochi": { lat: 9.9312, lon: 76.2673 },
    "Visakhapatnam": { lat: 17.6869, lon: 83.2185 },
    "Coimbatore": { lat: 11.0081, lon: 76.9877 },
    "Mysore": { lat: 12.2958, lon: 76.6394 },
    "Kurnool": { lat: 15.8281, lon: 78.8353 },
    "Vijayawada": { lat: 16.5062, lon: 80.6480 },
    "Tirupati": { lat: 13.1939, lon: 79.8245 },
    "Thanjavur": { lat: 10.7870, lon: 79.1378 },
    "Madurai": { lat: 9.9252, lon: 78.1198 },
    "Salem": { lat: 11.6643, lon: 78.1460 },
    "Thiruvananthapuram": { lat: 8.5241, lon: 76.9366 },
    "Warangal": { lat: 17.9784, lon: 79.6005 },
    // West India
    "Mumbai": { lat: 19.0760, lon: 72.8777 },
    "Pune": { lat: 18.5204, lon: 73.8567 },
    "Ahmedabad": { lat: 23.0225, lon: 72.5714 },
    "Surat": { lat: 21.1702, lon: 72.8311 },
    "Vadodara": { lat: 22.3072, lon: 73.1812 },
    "Rajkot": { lat: 22.3039, lon: 70.8022 },
    "Nashik": { lat: 19.9975, lon: 73.7898 },
    "Aurangabad": { lat: 19.8762, lon: 75.3433 },
    "Nagpur": { lat: 21.1458, lon: 79.0882 },
    "Thane": { lat: 19.2183, lon: 72.9781 },
    "Navi Mumbai": { lat: 19.0330, lon: 73.0297 },
    "Pimpri-Chinchwad": { lat: 18.6298, lon: 73.7997 },
    "Solapur": { lat: 17.6599, lon: 75.9064 },
    "Hubli-Dharwad": { lat: 15.3647, lon: 75.1240 },
    // East India
    "Kolkata": { lat: 22.5726, lon: 88.3639 },
    "Patna": { lat: 25.5941, lon: 85.1376 },
    "Ranchi": { lat: 23.3441, lon: 85.3096 },
    "Guwahati": { lat: 26.1445, lon: 91.7362 },
    "Raipur": { lat: 21.2514, lon: 81.6296 },
    "Bhubaneswar": { lat: 20.2961, lon: 85.8245 },
    "Jamshedpur": { lat: 22.8046, lon: 86.1855 },
    "Asansol": { lat: 23.6840, lon: 86.9640 },
    "Dhanbad": { lat: 23.7957, lon: 86.4304 },
    "Howrah": { lat: 22.5958, lon: 88.2636 },
    // Central India
    "Indore": { lat: 22.7196, lon: 75.8577 },
    "Bhopal": { lat: 23.1815, lon: 79.9864 },
    "Jabalpur": { lat: 23.1815, lon: 79.9864 },
    "Gwalior": { lat: 26.2183, lon: 78.1627 },
    "Ujjain": { lat: 23.1815, lon: 75.7854 },
    // North-East India
    "Imphal": { lat: 24.8170, lon: 94.9042 },
    "Shillong": { lat: 25.5729, lon: 91.8933 },
    "Agartala": { lat: 23.8103, lon: 91.2868 },
    "Dibrugarh": { lat: 27.4728, lon: 94.9103 }
};

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

// Small utility helpers
const sleep = (ms) => new Promise(res => setTimeout(res, ms));

// Rate-limit aware current AQI fetch with cache + backoff for 429s
async function fetchAQICurrentWithBackoff(cityName, retries = 1, delayMs = 700) {
    const nowGlobal = Date.now();
    if (nowGlobal < RATE_LIMITED_UNTIL) {
        // Respect global cooldown: skip hitting endpoint until window expires
        return null;
    }
    const key = (cityName || '').toLowerCase();
    const now = Date.now();
    const cached = currentAQICache.get(key);
    if (cached && (now - cached.ts) < AQI_CACHE_TTL_MS) {
        return cached.data;
    }
    try {
        const resp = await fetch(`${API_BASE_URL}/aqi/current/${encodeURIComponent(cityName)}`);
        if (resp.status === 429) {
            // Activate a 2 minute global cooldown and attempt limited retry if allowed
            RATE_LIMITED_UNTIL = Date.now() + (2 * 60 * 1000);
            if (retries > 0) {
                await sleep(delayMs);
                return fetchAQICurrentWithBackoff(cityName, retries - 1, delayMs * 1.5);
            }
            return null;
        }
        if (!resp.ok) return null;
        const data = await resp.json();
        currentAQICache.set(key, { data, ts: now });
        return data;
    } catch (_) {
        return null;
    }
}

// Single request endpoint fetching all cities current AQI (if backend supports it)
async function fetchAllCurrentAQI() {
    const nowGlobal = Date.now();
    if (nowGlobal < RATE_LIMITED_UNTIL) return null;
    try {
        const resp = await fetch(`${API_BASE_URL}/aqi/all/current`);
        if (resp.status === 429) {
            RATE_LIMITED_UNTIL = Date.now() + (2 * 60 * 1000);
            return null;
        }
        if (!resp.ok) return null;
        const json = await resp.json();
        const rows = Array.isArray(json?.data) ? json.data : [];
        // Prime cache
        rows.forEach(r => {
            if (r && r.city) {
                currentAQICache.set(r.city.toLowerCase(), { data: r, ts: Date.now() });
            }
        });
        return rows;
    } catch (_) {
        return null;
    }
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
        // Initialize all dashboard components
        initializeDashboard();
        loadCitiesForTrends();
        loadCitiesForComparison();
        loadCitiesForAlerts();
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
        
        // Get current AQI for a sample of cities using BATCH endpoint
        const sampleCities = cities.slice(0, 10);
        const cityNames = sampleCities.map(c => c.name).join(',');
        
        let batchUsed = false;
        if (BATCH_SUPPORTED !== false) {
            try {
                const batchResp = await fetch(`${API_BASE_URL}/aqi/batch?cities=${encodeURIComponent(cityNames)}`);
                if (batchResp.ok) {
                    const batchData = await batchResp.json();
                    const validAqi = (batchData.data || []).filter(d => (d.aqi || d.aqi_value));
                    if (validAqi.length > 0) {
                        const avgAqi = Math.round(validAqi.reduce((sum, d) => sum + (d.aqi || d.aqi_value), 0) / validAqi.length);
                        const avgAqiEl = document.getElementById('currentAvgAQI');
                        if (avgAqiEl) avgAqiEl.textContent = avgAqi;
                    }
                    BATCH_SUPPORTED = true;
                    batchUsed = true;
                } else if (batchResp.status === 404) {
                    // Mark as unsupported to avoid repeated 404 hits
                    BATCH_SUPPORTED = false;
                    console.warn('Batch endpoint 404 (home stats) - disabling further batch attempts');
                }
            } catch (err) {
                console.warn('Batch endpoint error (home stats):', err);
            }
        }

        // Fallback: attempt single all-cities endpoint; if unavailable perform very limited per-city fetches
        if (!batchUsed) {
            const allRows = await fetchAllCurrentAQI();
            if (Array.isArray(allRows) && allRows.length) {
                const sampleSet = new Set(sampleCities.map(c => c.name.toLowerCase()));
                const values = allRows
                    .filter(r => r.city && sampleSet.has(r.city.toLowerCase()))
                    .map(r => Number(r.aqi ?? r.aqi_value ?? 0))
                    .filter(v => v > 0);
                if (values.length) {
                    const avg = Math.round(values.reduce((a, b) => a + b, 0) / values.length);
                    const avgAqiEl = document.getElementById('currentAvgAQI');
                    if (avgAqiEl) avgAqiEl.textContent = avg;
                }
            } else {
                // Rate-limit conscious per-city fallback (smaller set, longer delays)
                const limited = sampleCities.slice(0, 3);
                const results = [];
                for (const city of limited) {
                    const data = await fetchAQICurrentWithBackoff(city.name, 1, 900);
                    if (data && (data.aqi || data.aqi_value)) {
                        results.push(data.aqi || data.aqi_value);
                    }
                    await sleep(600); // spread calls
                }
                if (results.length) {
                    const avg = Math.round(results.reduce((a, b) => a + b, 0) / results.length);
                    const avgAqiEl = document.getElementById('currentAvgAQI');
                    if (avgAqiEl) avgAqiEl.textContent = avg;
                }
            }
        }
        
        // Update data sources (OpenWeather API, IQAir - 2 sources)
        const dataSourcesEl = document.getElementById('dataSources');
        if (dataSourcesEl) dataSourcesEl.textContent = '2';
        
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
        if (!cities.length) return;

        // Take a sample of top cities using BATCH endpoint
        const topCities = cities.slice(0, 8);
        const cityNames = topCities.map(c => c.name).join(',');
        
        let cityData = [];
        let batchUsed = false;
        if (BATCH_SUPPORTED !== false) {
            try {
                const batchResp = await fetch(`${API_BASE_URL}/aqi/batch?cities=${encodeURIComponent(cityNames)}`);
                if (batchResp.ok) {
                    const batchData = await batchResp.json();
                    cityData = (batchData.data || []).map(d => ({
                        name: d.city,
                        aqi: d.aqi_value || d.aqi || 0,
                        category: getAQICategory(d.aqi_value || d.aqi || 0)
                    })).filter(d => d.aqi > 0);
                    BATCH_SUPPORTED = true;
                    batchUsed = true;
                } else if (batchResp.status === 404) {
                    BATCH_SUPPORTED = false;
                    console.warn('Batch endpoint 404 (top cities) - disabling further batch attempts');
                }
            } catch (err) {
                console.warn('Batch endpoint error (top cities):', err);
            }
        }

        if (!batchUsed) {
            const allRows = await fetchAllCurrentAQI();
            if (Array.isArray(allRows) && allRows.length) {
                const topSet = new Set(topCities.map(c => c.name.toLowerCase()));
                cityData = allRows
                    .filter(r => r.city && topSet.has(r.city.toLowerCase()))
                    .map(r => {
                        const val = Number(r.aqi ?? r.aqi_value ?? 0);
                        return val > 0 ? { name: r.city, aqi: val, category: getAQICategory(val) } : null;
                    })
                    .filter(Boolean);
            } else {
                const limited = topCities.slice(0, 3);
                const tempData = [];
                for (const city of limited) {
                    const data = await fetchAQICurrentWithBackoff(city.name, 1, 900);
                    if (data && (data.aqi || data.aqi_value)) {
                        const aqiVal = data.aqi || data.aqi_value || 0;
                        tempData.push({
                            name: city.name,
                            aqi: aqiVal,
                            category: getAQICategory(aqiVal)
                        });
                    }
                    await sleep(600);
                }
                cityData = tempData;
            }
        }

        const grid = document.getElementById('topCitiesGrid');
        if (!grid) return;
        if (!cityData.length) {
            grid.innerHTML = '<div class="no-data">No AQI data available</div>';
            return;
        }
        grid.innerHTML = cityData.map(d => `
            <div class="city-card">
                <div class="city-name">${d.name}</div>
                <div class="aqi-display ${getAQIColorClass(d.aqi)}">${d.aqi}</div>
                <div style="text-align:center;font-size:0.85em;color:#333;">${d.category}</div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading top cities:', err);
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

// Trends Functions (robust handling for backend response shapes)
async function loadHistoricalTrends() {
    try {
        const citySelect = document.getElementById('trendCity');
        const daysSelect = document.getElementById('trendDays');
        const city = citySelect?.value || 'Delhi';
        const days = daysSelect?.value || 30;
        if (!city) return;

        const resp = await fetch(`${API_BASE_URL}/aqi/history/${encodeURIComponent(city)}?days=${days}`);
        if (!resp.ok) throw new Error(`Failed to load history (${resp.status})`);
        const payload = await resp.json();

        // Support both formats: { data: [...] } or direct array [...]
        const rows = Array.isArray(payload) ? payload : (Array.isArray(payload?.data) ? payload.data : []);

        const aqiDiv = document.getElementById('aqiTrendChart');
        if (!aqiDiv) return;

        if (!Array.isArray(rows) || rows.length === 0) {
            aqiDiv.innerHTML = '<div class="no-data">No historical data</div>';
            const polDiv = document.getElementById('pollutantsTrendChart');
            if (polDiv) polDiv.innerHTML = '';
            return;
        }

        const getTs = (d) => d.timestamp || d.date || d.time;
        const getAQI = (d) => {
            if (typeof d.aqi === 'number') return d.aqi;
            if (typeof d.aqi_value === 'number') return d.aqi_value;
            if (typeof d.value === 'number') return d.value;
            return 0;
        };

        const x = rows.map(getTs);
        const y = rows.map(getAQI);

        if (typeof Plotly !== 'undefined') {
            // Main AQI trend
            Plotly.newPlot('aqiTrendChart', [{
                x,
                y,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'AQI',
                line: { color: '#10b981' }
            }], { title: `AQI Trend - ${city}`, height: 360, xaxis: { title: 'Time' }, yaxis: { title: 'AQI' } });

            // Optional pollutants trends if present
            const polDiv = document.getElementById('pollutantsTrendChart');
            if (polDiv) {
                const traces = [];
                const addTrace = (key, label, color) => {
                    const vals = rows.map(d => typeof d[key] === 'number' ? d[key] : null);
                    if (vals.some(v => v !== null)) {
                        traces.push({ x, y: vals, type: 'scatter', mode: 'lines', name: label, line: { color } });
                    }
                };
                addTrace('pm25', 'PM2.5', '#6366f1');
                addTrace('pm10', 'PM10', '#f59e0b');
                addTrace('no2', 'NO2', '#ef4444');
                addTrace('so2', 'SO2', '#10b981');
                addTrace('o3', 'O3', '#3b82f6');
                addTrace('co', 'CO', '#a855f7');

                if (traces.length) {
                    Plotly.newPlot('pollutantsTrendChart', traces, {
                        title: `Pollutants Trend - ${city}`,
                        height: 360,
                        xaxis: { title: 'Time' },
                        yaxis: { title: 'Concentration' },
                        legend: { orientation: 'h' }
                    });
                } else {
                    polDiv.innerHTML = '';
                }
            }
        } else {
            aqiDiv.innerHTML = '<div class="no-data">Plotly not loaded</div>';
        }
    } catch (err) {
        console.error('Error loading historical trends:', err);
        const aqiDiv = document.getElementById('aqiTrendChart');
        if (aqiDiv) aqiDiv.innerHTML = '<div class="error">Error loading trends</div>';
        const polDiv = document.getElementById('pollutantsTrendChart');
        if (polDiv) polDiv.innerHTML = '';
    }
}

// Dashboard tab switching
function switchDashboardTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.dashboard-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`dashboard-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Activate button
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        if (btn.textContent.toLowerCase().includes(tabName)) {
            btn.classList.add('active');
        }
    });
    
    // Initialize tab-specific features
    if (tabName === 'map') {
        initializeDashboard();
    } else if (tabName === 'trends') {
        loadCitiesForTrends();
    } else if (tabName === 'comparison') {
        loadCitiesForComparison();
    } else if (tabName === 'alerts') {
        loadCitiesForAlerts();
        loadUserAlerts();
    }
}

// Initialize dashboard with live map and rankings
async function initializeDashboard() {
    try {
        // Avoid heavy re-initialization if already set up
        if (liveInitialized) {
            // Still ensure rankings chart exists once per session
            if (!document.getElementById('rankingsChart')) return;
        }
        const cities = await getCities();
        if (!cities.length) return;
        
        // Load rankings chart using batch endpoint for speed
        const rankingsCities = cities.slice(0, 10); // limit initial load for speed
        const cityNames = rankingsCities.map(c => c.name).join(',');
        
        let rankingData = [];
        try {
            const batchResp = await fetch(`${API_BASE_URL}/aqi/batch?cities=${encodeURIComponent(cityNames)}`);
            if (batchResp.ok) {
                const batchData = await batchResp.json();
                console.log('Rankings batch response:', batchData);
                // Handle both aqi and aqi_value field names
                rankingData = (batchData.data || [])
                    .map(d => {
                        const aqi = d.aqi_value || d.aqi;
                        return aqi != null && aqi > 0 ? { city: d.city, aqi: aqi } : null;
                    })
                    .filter(Boolean); // Filter out null entries
                
                console.log(`Rankings: ${rankingData.length} cities with valid AQI data`);
                
                // Cache the results
                batchData.data?.forEach(d => {
                    const key = (d.city || '').toLowerCase();
                    currentAQICache.set(key, { data: d, ts: Date.now() });
                });
            } else {
                console.error('Batch endpoint returned error:', batchResp.status);
                throw new Error(`HTTP ${batchResp.status}`);
            }
        } catch (batchErr) {
            console.warn('Batch endpoint failed, falling back to individual requests:', batchErr);
            // Fallback to individual requests
            const rankingPromises = rankingsCities.map(async city => {
                try {
                    const data = await fetchCurrentAQI(city.name);
                    const aqi = data?.aqi_value || data?.aqi || 0;
                    return aqi > 0 ? { city: city.name, aqi } : null;
                } catch (_) { return null; }
            });
            rankingData = (await Promise.all(rankingPromises)).filter(Boolean);
        }
        
        rankingData.sort((a, b) => b.aqi - a.aqi);
        
        console.log('Rankings data to display:', rankingData);
        
        if (rankingData.length && typeof Plotly !== 'undefined') {
            const rankingsChart = document.getElementById('rankingsChart');
            if (rankingsChart) {
                try {
                    Plotly.newPlot('rankingsChart', [{
                        x: rankingData.map(d => d.city),
                        y: rankingData.map(d => d.aqi),
                        type: 'bar',
                        marker: {
                            color: rankingData.map(d => getAQIColor(d.aqi))
                        }
                    }], {
                        title: 'Cities by AQI Level',
                        xaxis: { title: 'City' },
                        yaxis: { title: 'AQI' },
                        height: 400
                    });
                    console.log('Rankings chart rendered successfully');
                } catch (plotErr) {
                    console.error('Error rendering rankings chart:', plotErr);
                }
            } else {
                console.warn('Rankings chart element not found');
            }
        } else {
            if (!rankingData.length) {
                console.warn('No ranking data available to display');
            }
            if (typeof Plotly === 'undefined') {
                console.warn('Plotly library not loaded');
            }
        }
        
        // Initialize Leaflet map with AQI markers if library loaded
        if (typeof L !== 'undefined') {
            try {
                if (!currentMap) {
                    currentMap = L.map('map').setView([22.9734, 78.6569], 5); // Center India
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        maxZoom: 10,
                        attribution: '&copy; OpenStreetMap contributors'
                    }).addTo(currentMap);
                }

                // Clear existing markers layer if needed
                if (currentMap._aqiLayer) {
                    currentMap.removeLayer(currentMap._aqiLayer);
                }
                const layerGroup = L.layerGroup();

                // Show all cities on the map using batch endpoint for faster loading
                const mapCities = cities;

                // Try batch endpoint first for all cities
                try {
                    const cityNames = mapCities.map(c => c.name || c.city || c).join(',');
                    const batchResp = await fetch(`${API_BASE_URL}/aqi/batch?cities=${encodeURIComponent(cityNames)}`);
                    
                    if (batchResp.ok) {
                        const batchData = await batchResp.json();
                        console.log('Batch AQI response:', batchData);
                        const aqiByCity = new Map();
                        
                        // Cache batch results
                        if (batchData.data && Array.isArray(batchData.data)) {
                            batchData.data.forEach(item => {
                                const cityKey = item.city?.toLowerCase();
                                if (cityKey) {
                                    aqiByCity.set(cityKey, item);
                                    currentAQICache.set(cityKey, {
                                        data: item,
                                        timestamp: Date.now()
                                    });
                                }
                            });
                        }

                        console.log(`Map: Processing ${mapCities.length} cities, batch returned ${aqiByCity.size} with data`);

                        // Create markers for all cities
                        let markersCreated = 0;
                        mapCities.forEach(city => {
                            const name = city.name || city.city || city;
                            let lat = city.lat || city.latitude || (CITY_COORDS[name]?.lat);
                            let lon = city.lon || city.lng || city.longitude || (CITY_COORDS[name]?.lon);
                            if (lat == null || lon == null) {
                                console.warn(`No coordinates for ${name}`);
                                return;
                            }

                            const data = aqiByCity.get(name.toLowerCase());
                            if (!data) {
                                console.warn(`No AQI data for ${name}`);
                                return;
                            }

                            // Handle both aqi and aqi_value field names
                            const aqi = data.aqi_value || data.aqi;
                            if (aqi == null || aqi <= 0) {
                                console.warn(`Invalid AQI (${aqi}) for ${name}`, data);
                                return;
                            }

                            const color = getAQIColor(aqi);
                            const category = getAQICategory(aqi);
                            const marker = L.circleMarker([lat, lon], {
                                radius: 10,
                                color: '#222',
                                weight: 1,
                                fillColor: color,
                                fillOpacity: 0.85
                            }).bindPopup(`
                                <div style="min-width:160px;font-family:inherit;">
                                    <strong>${name}</strong><br>
                                    AQI: <span style="font-weight:600;color:${color}">${aqi}</span><br>
                                    <small>${category}</small>
                                </div>
                            `);
                            layerGroup.addLayer(marker);
                            markersCreated++;
                        });
                        
                        console.log(`Created ${markersCreated} markers on map`);
                    } else {
                        throw new Error('Batch endpoint failed, falling back');
                    }
                } catch (batchErr) {
                    console.warn('Batch map loading failed, using individual fetches:', batchErr);
                    
                    // Fallback: individual fetches with concurrency limiting
                    const worker = async (city) => {
                        const name = city.name || city.city || city;
                        let lat = city.lat || city.latitude || (CITY_COORDS[name]?.lat);
                        let lon = city.lon || city.lng || city.longitude || (CITY_COORDS[name]?.lon);
                        if (lat == null || lon == null) return;
                        try {
                            const data = await fetchCurrentAQI(name);
                            const aqi = data?.aqi || 0;
                            const color = getAQIColor(aqi);
                            const category = getAQICategory(aqi);
                            const marker = L.circleMarker([lat, lon], {
                                radius: 10,
                                color: '#222',
                                weight: 1,
                                fillColor: color,
                                fillOpacity: 0.85
                            }).bindPopup(`
                                <div style="min-width:160px;font-family:inherit;">
                                    <strong>${name}</strong><br>
                                    AQI: <span style="font-weight:600;color:${color}">${aqi}</span><br>
                                    <small>${category}</small>
                                </div>
                            `);
                            layerGroup.addLayer(marker);
                        } catch (_) { /* ignore */ }
                    };

                    const CONCURRENCY = 10; // Increased concurrency since we're loading all cities
                    let i = 0;
                    const runners = new Array(CONCURRENCY).fill(0).map(async () => {
                        while (i < mapCities.length) {
                            const idx = i++;
                            await worker(mapCities[idx]);
                        }
                    });
                    await Promise.all(runners);
                }

                layerGroup.addTo(currentMap);
                currentMap._aqiLayer = layerGroup;

                // Add legend
                if (!currentMap._aqiLegend) {
                    const legend = L.control({ position: 'bottomright' });
                    legend.onAdd = function () {
                        const div = L.DomUtil.create('div', 'aqi-legend');
                        const ranges = [
                            { max: 100, label: 'Good' },
                            { max: 200, label: 'Moderate' },
                            { max: 300, label: 'Unhealthy' },
                            { max: 400, label: 'Very Unhealthy' },
                            { max: 500, label: 'Hazardous' }
                        ];
                        div.style.background = 'white';
                        div.style.padding = '10px';
                        div.style.borderRadius = '8px';
                        div.style.boxShadow = '0 2px 6px rgba(0,0,0,0.2)';
                        div.style.fontSize = '12px';
                        div.innerHTML = '<strong>AQI Legend</strong><br>' + ranges.map(r => {
                            return `<div style="display:flex;align-items:center;gap:6px;margin-top:4px;">
                                <span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:${getAQIColor(r.max)}"></span>${r.label}
                            </div>`;
                        }).join('');
                        return div;
                    };
                    legend.addTo(currentMap);
                    currentMap._aqiLegend = legend;
                }
            } catch (mapErr) {
                console.error('Map setup error:', mapErr);
            }
        } else {
            console.warn('Leaflet not loaded; map skipped');
        }

        liveInitialized = true;
        
    } catch (err) {
        console.error('Error initializing dashboard:', err);
    }
}

// Cached fetch for current AQI per city with TTL to reduce duplicate requests
async function fetchCurrentAQI(cityName) {
    const key = (cityName || '').toLowerCase();
    const now = Date.now();
    const cached = currentAQICache.get(key);
    if (cached && (now - cached.ts) < AQI_CACHE_TTL_MS) {
        return cached.data;
    }
    const resp = await fetch(`${API_BASE_URL}/aqi/current/${encodeURIComponent(cityName)}`);
    if (!resp.ok) throw new Error(`AQI fetch failed ${resp.status}`);
    const data = await resp.json();
    currentAQICache.set(key, { data, ts: now });
    return data;
}

// City comparison
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
    
    // Update UI
    const buttons = document.querySelectorAll('.city-selector');
    buttons.forEach(btn => {
        const city = btn.textContent.trim();
        if (selectedCities.includes(city)) {
            btn.classList.add('selected');
        } else {
            btn.classList.remove('selected');
        }
    });
    
    // Load comparison
    if (selectedCities.length > 0) {
        loadCityComparison();
    }
}

async function loadCityComparison() {
    if (selectedCities.length === 0) return;
    
    const grid = document.getElementById('comparisonGrid');
    const chart = document.getElementById('comparisonChart');
    
    if (grid) grid.innerHTML = '<div class="loading">Loading comparison...</div>';
    
    try {
        const dataPromises = selectedCities.map(async city => {
            try {
                const resp = await fetch(`${API_BASE_URL}/aqi/current/${city}`);
                if (!resp.ok) return null;
                const data = await resp.json();
                return {
                    city,
                    aqi: data.aqi || 0,
                    pm25: data.pm25 || data.pollutants?.pm25 || 0,
                    pm10: data.pm10 || data.pollutants?.pm10 || 0,
                    category: getAQICategory(data.aqi || 0)
                };
            } catch (_) { return null; }
        });
        
        const cityData = (await Promise.all(dataPromises)).filter(Boolean);
        
        if (!cityData.length) {
            if (grid) grid.innerHTML = '<div class="no-data">No data available</div>';
            return;
        }
        
        // Render comparison grid
        if (grid) {
            grid.innerHTML = cityData.map(d => `
                <div class="city-card">
                    <div class="city-name">${d.city}</div>
                    <div class="aqi-display ${getAQIColorClass(d.aqi)}">${d.aqi}</div>
                    <div style="text-align:center;font-size:0.85em;color:#333;">${d.category}</div>
                    <div style="margin-top:8px;font-size:0.8em;color:#666;">
                        PM2.5: ${d.pm25.toFixed(1)} | PM10: ${d.pm10.toFixed(1)}
                    </div>
                </div>
            `).join('');
        }
        
        // Render comparison chart
        if (chart && typeof Plotly !== 'undefined') {
            Plotly.newPlot('comparisonChart', [{
                x: cityData.map(d => d.city),
                y: cityData.map(d => d.aqi),
                type: 'bar',
                marker: {
                    color: cityData.map(d => getAQIColor(d.aqi))
                },
                text: cityData.map(d => d.aqi),
                textposition: 'auto'
            }], {
                title: 'AQI Comparison',
                xaxis: { title: 'City' },
                yaxis: { title: 'AQI' },
                height: 400
            });
        }
        
    } catch (err) {
        console.error('Error loading city comparison:', err);
        if (grid) grid.innerHTML = '<div class="error">Error loading comparison</div>';
    }
}

// Alert creation
async function createAlert(event) {
    if (event) event.preventDefault();
    
    const city = document.getElementById('alertCity')?.value;
    const email = document.getElementById('alertEmail')?.value;
    const threshold = document.getElementById('alertThreshold')?.value;
    
    if (!city || !email || !threshold) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const resp = await fetch(`${API_BASE_URL}/alerts/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                city,
                contact: email,
                threshold: parseInt(threshold, 10),
                alert_type: 'email'
            })
        });
        
        if (resp.ok) {
            alert('Alert created successfully!');
            document.getElementById('alertForm')?.reset();
            loadUserAlerts();
        } else {
            const error = await resp.text();
            alert(`Error creating alert: ${error}`);
        }
    } catch (err) {
        console.error('Error creating alert:', err);
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
        
        // Corrected container ID (was healthInfo, actual HTML uses healthContent)
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
    if (aqi <= 100) {
        return {
            impact: 'Good - Air quality is satisfactory',
            recommendations: [
                'Ideal conditions for outdoor activities',
                'No health precautions needed',
                'Air quality is considered satisfactory'
            ],
            atRisk: 'None'
        };
    } else if (aqi <= 200) {
        return {
            impact: 'Moderate - Acceptable air quality',
            recommendations: [
                'Unusually sensitive people should limit prolonged outdoor exertion',
                'General population can enjoy outdoor activities',
                'Consider reducing time outdoors if you are sensitive'
            ],
            atRisk: 'Unusually sensitive individuals'
        };
    } else if (aqi <= 300) {
        return {
            impact: 'Unhealthy - Everyone may experience health effects',
            recommendations: [
                'Limit outdoor activities',
                'Wear N95/N99 masks when going outside',
                'Use air purifiers indoors',
                'Avoid strenuous activities',
                'Keep windows closed'
            ],
            atRisk: 'Everyone, especially sensitive groups'
        };
    } else if (aqi <= 400) {
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
    const hoursSelect = document.getElementById('forecastHours');
    const hours = hoursSelect ? parseInt(hoursSelect.value, 10) : 24;

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
        const predictionResponse = await fetch(`${API_BASE_URL}/forecast/${city}?hours=${hours}`);

        if (!predictionResponse.ok) {
            if (predictionResponse.status === 404) {
                // Graceful no-data handling
                predictionData = { forecast: [], predicted_aqi: 0, confidence: 'N/A', forecast_hours: hours };
                displayCurrentVsPredicted();
                displayPredictionChartNoData(city);
                displayHourlyForecastNoData();
                return; 
            }
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
            const horizonIndex = Math.min((hours || predictionData.forecast_hours || predictionData.forecast.length) - 1, predictionData.forecast.length - 1);
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
    displayPredictionChart(hours);
    displayPollutants();
    displayHourlyForecast(hours);
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
    if (currentTimestamp) {
        const ts = new Date(currentData.timestamp);
        currentTimestamp.textContent = ts.toLocaleString();
        // Append data age if available
        if (typeof currentData.data_age_hours === 'number') {
            const hrs = Math.floor(currentData.data_age_hours);
            const mins = Math.round((currentData.data_age_hours - hrs) * 60);
            const ageText = ` • Updated ${hrs}h ${mins}m ago`;
            currentTimestamp.textContent += ageText;
        }
    }
    
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

function displayPredictionChartNoData(city) {
    const chart = document.getElementById('forecastChart');
    if (chart) {
        chart.innerHTML = `<div class="no-data">No recent data available for ${city}. Forecast cannot be generated.</div>`;
    }
    const predictionHoursEl = document.getElementById('predictionHours');
    if (predictionHoursEl) predictionHoursEl.textContent = '--';
    const aqiChange = document.getElementById('aqiChange');
    if (aqiChange) {
        aqiChange.textContent = 'No change (insufficient data)';
        aqiChange.className = 'change-indicator';
    }
}

function displayHourlyForecastNoData() {
    const tbody = document.getElementById('hourlyTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="4" class="no-data">No data to forecast</td></tr>';
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

    container.innerHTML = '<div class="loading">Loading active training performance...</div>';
    try {
        const resp = await fetch(`${API_BASE_URL}/models/active_training`);
        if (!resp.ok) {
            container.innerHTML = '<div class="error">No training performance available.</div>';
            return;
        }
        const data = await resp.json();
        if (activeModelEl) activeModelEl.textContent = (data.active_model || 'N/A').toUpperCase();
        const r2 = typeof data.training_r2 === 'number' ? data.training_r2.toFixed(3) : '--';
        const rmse = typeof data.metrics?.rmse === 'number' ? data.metrics.rmse.toFixed(2) : '--';
        const mae = typeof data.metrics?.mae === 'number' ? data.metrics.mae.toFixed(2) : '--';
        container.innerHTML = `
            <div class="metric-card best-model-card">
                <div class="metric-header">
                    <span class="model-name">${data.active_model || 'UNKNOWN MODEL'}</span>
                </div>
                <div class="metric-grid">
                    <div class="metric-item">
                        <span class="metric-label">Training R²</span>
                        <span class="metric-value">${r2}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">RMSE</span>
                        <span class="metric-value">${rmse}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">MAE</span>
                        <span class="metric-value">${mae}</span>
                    </div>
                </div>
                <div class="metrics-legend" style="margin-top:8px;">
                    <p style="margin:0;font-size:0.85em;color:#555;">Training metrics loaded from saved file (${data.source || 'n/a'}). Only training performance is shown as requested.</p>
                </div>
            </div>`;
    } catch (err) {
        console.error('Error loading active training performance:', err);
        container.innerHTML = '<div class="error">Failed to load active model performance.</div>';
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getAQIColor(aqi) {
    if (aqi <= 100) return '#00e400';
    if (aqi <= 200) return '#ffff00';
    if (aqi <= 300) return '#ff7e00';
    if (aqi <= 400) return '#ff0000';
    if (aqi <= 500) return '#8f3f97';
    return '#7e0023';
}

function getAQIColorClass(aqi) {
    if (aqi <= 100) return 'aqi-good';
    if (aqi <= 200) return 'aqi-moderate';
    if (aqi <= 300) return 'aqi-unhealthy';
    if (aqi <= 400) return 'aqi-very-unhealthy';
    if (aqi <= 500) return 'aqi-hazardous';
    return 'aqi-hazardous';
}

function getAQICategory(aqi) {
    if (aqi <= 100) return 'Good';
    if (aqi <= 200) return 'Moderate';
    if (aqi <= 300) return 'Unhealthy';
    if (aqi <= 400) return 'Very Unhealthy';
    if (aqi <= 500) return 'Hazardous';
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
        
        // Show initial message
        const grid = document.getElementById('comparisonGrid');
        if (grid && selectedCities.length === 0) {
            grid.innerHTML = '<div class="no-data" style="text-align: center; padding: 40px;">👆 Select cities above to compare their air quality</div>';
        }
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

async function loadCitiesForTrends() {
    try {
        const cities = await getCities();
        
        const select = document.getElementById('trendCity');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select a city...</option>' + cities.map(city => `
            <option value="${city.name}">${city.name}</option>
        `).join('');
        
        // Set default
        if (cities.length > 0) {
            select.value = cities[0].name;
            loadHistoricalTrends();
        }
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
        
        // Also load for health selector
        const healthSelect = document.getElementById('healthCity');
        if (healthSelect) {
            healthSelect.innerHTML = '<option value="">Select a city...</option>' + cities.map(city => `
                <option value="${city.name}">${city.name}</option>
            `).join('');
            // Set a default and load recommendations immediately
            if (cities.length) {
                healthSelect.value = cities[0].name;
                loadHealthRecommendations();
            }
        }
    } catch (error) {
        console.error('Error loading cities for alerts:', error);
    }
}
