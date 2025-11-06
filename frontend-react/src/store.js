import { create } from 'zustand';
import axios from 'axios';

// API Configuration - Use environment variables in production
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

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
      // Fallback: Use all cities endpoint and filter for the selected city
      // This works around the /aqi/current/{city} 500 error
      try {
        const response = await axios.get(`${API_BASE_URL}/aqi/current/${city}`);
        set({ currentAQI: response.data, error: null });
      } catch (primaryError) {
        // Fallback to all cities endpoint
        const allResponse = await axios.get(`${API_BASE_URL}/aqi/all/current`);
        const cityData = allResponse.data.data?.find(c => c.city === city);
        if (cityData) {
          set({ currentAQI: cityData, error: null });
        } else {
          throw new Error(`No data available for ${city}`);
        }
      }
    } catch (error) {
      set({ currentAQI: null, error: error.response?.data?.error || error.message });
    }
  },
  
  // Fetch forecast
  fetchForecast: async (city, hours = 48) => {
    try {
      set({ loading: true });
      const response = await axios.get(`${API_BASE_URL}/forecast/${city}?hours=${hours}`);
      set({ forecast: response.data.forecast || response.data, loading: false, error: null });
    } catch (error) {
      console.error('Forecast fetch error:', error);
      set({ forecast: null, loading: false, error: error.response?.data?.error || error.message });
    }
  },
  
  // Fetch historical data
  fetchHistoricalData: async (city, days = 1) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/aqi/history/${city}?days=${days}`);
      set({ historicalData: response.data.data || response.data.history || [], error: null });
    } catch (error) {
      console.error('Historical data fetch error:', error);
      set({ historicalData: [], error: error.response?.data?.error || error.message });
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
      set({ modelMetrics: response.data.metrics || response.data, error: null });
    } catch (error) {
      console.error('Model metrics fetch error:', error);
      set({ modelMetrics: null, error: error.response?.data?.error || error.message });
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
  
  // Load city data (combination of multiple fetches)
  loadCityData: async (city) => {
    const store = get();
    await Promise.all([
      store.fetchCurrentAQI(city),
      store.fetchForecast(city, 48),
      store.fetchHistoricalData(city, 1), // Changed from 7 to 1 day for 24-hour view
      store.fetchModelMetrics(city)
    ]);
  }
}));

export { useStore };
export default useStore;
