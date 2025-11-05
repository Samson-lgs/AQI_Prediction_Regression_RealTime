import { create } from 'zustand';
import axios from 'axios';
import { io } from 'socket.io-client';

// API Configuration - Use environment variables in production
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const SOCKET_URL = import.meta.env.VITE_WS_URL || 'http://localhost:5000';

// Socket.IO client
let socket = null;

const useStore = create((set, get) => ({
  // State
  cities: [],
  selectedCity: 'Delhi',
  currentAQI: null,
  forecast: null,
  historicalData: [],
  cityComparison: null,
  rankings: [],
  allCitiesCurrent: [],
  modelMetrics: null,
  loading: false,
  error: null,
  connected: false,
  
  // Actions
  setSelectedCity: (city) => set({ selectedCity: city }),
  
  setLoading: (loading) => set({ loading }),
  
  setError: (error) => set({ error }),
  
  // Fetch cities list
  fetchCities: async () => {
    try {
      set({ loading: true, error: null });
      const response = await axios.get(`${API_BASE_URL}/cities/`);
      // API returns array directly, not wrapped in object
      const citiesData = Array.isArray(response.data) ? response.data : [];
      set({ cities: citiesData, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
      set({ cities: [] }); // Ensure cities is always an array
    }
  },
  
  // Fetch current AQI for selected city
  fetchCurrentAQI: async (city) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/aqi/current/${city}`);
      set({ currentAQI: response.data, error: null });
    } catch (error) {
      set({ currentAQI: null, error: error.response?.data?.error || error.message });
    }
  },
  
  // Fetch forecast
  fetchForecast: async (city, hours = 48) => {
    try {
      set({ loading: true });
      const response = await axios.get(`${API_BASE_URL}/forecast/${city}?hours=${hours}`);
      set({ forecast: response.data, loading: false, error: null });
    } catch (error) {
      set({ forecast: null, loading: false, error: error.message });
    }
  },
  
  // Fetch historical data
  fetchHistoricalData: async (city, days = 7) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/aqi/history/${city}?days=${days}`);
      set({ historicalData: response.data.data || [], error: null });
    } catch (error) {
      set({ historicalData: [], error: error.message });
    }
  },
  
  // Fetch city rankings
  fetchRankings: async (days = 7, metric = 'avg_aqi') => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cities/rankings?days=${days}&metric=${metric}`);
      set({ rankings: response.data.rankings || [], error: null });
    } catch (error) {
      set({ rankings: [], error: error.message });
    }
  },
  
  // Compare cities
  compareCities: async (cities, days = 7) => {
    try {
      const citiesParam = cities.join(',');
      const response = await axios.get(`${API_BASE_URL}/cities/compare?cities=${citiesParam}&days=${days}`);
      set({ cityComparison: response.data.comparison, error: null });
    } catch (error) {
      set({ cityComparison: null, error: error.message });
    }
  },
  
  // Fetch model metrics
  fetchModelMetrics: async (city, model = 'xgboost') => {
    try {
      const response = await axios.get(`${API_BASE_URL}/models/performance/${city}?model=${model}`);
      set({ modelMetrics: response.data.metrics, error: null });
    } catch (error) {
      set({ modelMetrics: null, error: error.message });
    }
  },

  // Fetch all cities current AQI for map view
  fetchAllCitiesCurrent: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/aqi/all/current`);
      const data = Array.isArray(response.data?.data) ? response.data.data : [];
      set({ allCitiesCurrent: data, error: null });
    } catch (error) {
      set({ allCitiesCurrent: [], error: error.message });
    }
  },
  
  // Batch forecast
  batchForecast: async (cities, hours = 24) => {
    try {
      set({ loading: true });
      const response = await axios.post(`${API_BASE_URL}/forecast/batch`, {
        cities,
        hours_ahead: hours
      });
      set({ loading: false });
      return response.data;
    } catch (error) {
      set({ loading: false, error: error.message });
      return null;
    }
  },
  
  // WebSocket connection
  connectWebSocket: () => {
    if (socket) return;
    
    socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });
    
    socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      set({ connected: true, error: null });
    });
    
    socket.on('connect_error', (error) => {
      console.log('⚠️ WebSocket connection error:', error.message);
      set({ connected: false });
    });
    
    socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
      set({ connected: false });
    });
    
    socket.on('aqi_update', (data) => {
      const { selectedCity, currentAQI } = get();
      if (data.city === selectedCity) {
        set({ 
          currentAQI: { 
            ...currentAQI, 
            ...data,
            timestamp: new Date(data.timestamp).toISOString()
          } 
        });
      }
    });
    
    socket.on('prediction_update', (data) => {
      console.log('Prediction update:', data);
    });
    
    socket.on('aqi_alert', (data) => {
      console.log('AQI Alert:', data);
      // Could trigger a notification here
    });
  },
  
  disconnectWebSocket: () => {
    if (socket) {
      socket.disconnect();
      socket = null;
      set({ connected: false });
    }
  },
  
  subscribeToCity: (city) => {
    if (socket && socket.connected) {
      socket.emit('subscribe_city', { city });
    }
  },
  
  unsubscribeFromCity: (city) => {
    if (socket && socket.connected) {
      socket.emit('unsubscribe_city', { city });
    }
  },
  
  // Load city data (combination of multiple fetches)
  loadCityData: async (city) => {
    const store = get();
    await Promise.all([
      store.fetchCurrentAQI(city),
      store.fetchForecast(city, 48),
      store.fetchHistoricalData(city, 7),
      store.fetchModelMetrics(city)
    ]);
  }
}));

export { useStore };
export default useStore;
