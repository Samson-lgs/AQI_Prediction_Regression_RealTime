// API endpoints
const API_BASE_URL = 'http://localhost:8000';

// Chart configuration
let aqiChart;

// Initialize the chart
function initializeChart() {
    const ctx = document.getElementById('aqiChart').getContext('2d');
    aqiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'AQI Values',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Fetch data from the backend
async function getData() {
    const city = document.getElementById('cityInput').value;
    if (!city) {
        alert('Please enter a city name');
        return;
    }

    try {
        // Get current AQI
        const aqiResponse = await fetch(`${API_BASE_URL}/aqi/${city}`);
        const aqiData = await aqiResponse.json();
        
        // Get weather information
        const weatherResponse = await fetch(`${API_BASE_URL}/weather/${city}`);
        const weatherData = await weatherResponse.json();
        
        // Get prediction
        const predictionResponse = await fetch(`${API_BASE_URL}/prediction/${city}`);
        const predictionData = await predictionResponse.json();
        
        // Update the UI
        updateUI(aqiData, weatherData, predictionData);
        
    } catch (error) {
        console.error('Error fetching data:', error);
        alert('Error fetching data. Please try again.');
    }
}

// Update the UI with fetched data
function updateUI(aqiData, weatherData, predictionData) {
    // Update current AQI
    document.querySelector('#current-aqi .value').textContent = aqiData.aqi;
    
    // Update weather information
    const weatherInfo = `
        Temperature: ${weatherData.temp}°C
        Humidity: ${weatherData.humidity}%
        Wind Speed: ${weatherData.wind_speed} m/s
    `;
    document.querySelector('#weather-info .value').textContent = weatherInfo;
    
    // Update prediction
    document.querySelector('#prediction .value').textContent = 
        `Predicted AQI: ${predictionData.predicted_aqi}`;
    
    // Update chart
    updateChart(aqiData.historical_data);
}

// Update the chart with new data
function updateChart(historicalData) {
    const labels = historicalData.map(d => d.timestamp);
    const values = historicalData.map(d => d.aqi);
    
    aqiChart.data.labels = labels;
    aqiChart.data.datasets[0].data = values;
    aqiChart.update();
}

// Initialize chart when page loads
document.addEventListener('DOMContentLoaded', initializeChart);