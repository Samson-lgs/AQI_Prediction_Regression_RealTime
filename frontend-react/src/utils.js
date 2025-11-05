// AQI utility functions

export const getAQICategory = (aqi) => {
  if (aqi <= 50) return 'Good';
  if (aqi <= 100) return 'Satisfactory';
  if (aqi <= 200) return 'Moderate';
  if (aqi <= 300) return 'Poor';
  if (aqi <= 400) return 'Very Poor';
  return 'Severe';
};

export const getAQIColor = (aqi) => {
  if (aqi <= 50) return '#00e400';
  if (aqi <= 100) return '#ffff00';
  if (aqi <= 200) return '#ff7e00';
  if (aqi <= 300) return '#ff0000';
  if (aqi <= 400) return '#8f3f97';
  return '#7e0023';
};

export const getAQIBadgeClass = (aqi) => {
  if (aqi <= 50) return 'badge-good';
  if (aqi <= 100) return 'badge-satisfactory';
  if (aqi <= 200) return 'badge-moderate';
  if (aqi <= 300) return 'badge-poor';
  if (aqi <= 400) return 'badge-very-poor';
  return 'badge-severe';
};

export const getAQIDescription = (aqi) => {
  if (aqi <= 50) return 'Minimal impact';
  if (aqi <= 100) return 'Minor breathing discomfort to sensitive people';
  if (aqi <= 200) return 'Breathing discomfort to people with lung, heart disease';
  if (aqi <= 300) return 'Breathing discomfort to most people on prolonged exposure';
  if (aqi <= 400) return 'Respiratory illness on prolonged exposure';
  return 'Affects healthy people and seriously impacts those with existing diseases';
};

export const formatTimestamp = (timestamp) => {
  if (!timestamp) return '--';
  const date = new Date(timestamp);
  return date.toLocaleString('en-IN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatDate = (timestamp) => {
  if (!timestamp) return '--';
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

export const formatTime = (timestamp) => {
  if (!timestamp) return '--';
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const calculateChange = (current, previous) => {
  if (!current || !previous) return 0;
  return current - previous;
};

export const calculateChangePercent = (current, previous) => {
  if (!current || !previous || previous === 0) return 0;
  return ((current - previous) / previous * 100).toFixed(1);
};

export const getTrend = (change) => {
  if (change > 0) return 'increasing';
  if (change < 0) return 'decreasing';
  return 'stable';
};

export const getTrendIcon = (change) => {
  if (change > 5) return '↑↑';
  if (change > 0) return '↑';
  if (change < -5) return '↓↓';
  if (change < 0) return '↓';
  return '→';
};

export const getPollutantLimit = (pollutant) => {
  const limits = {
    pm25: { good: 30, moderate: 60, poor: 90, severe: 120 },
    pm10: { good: 50, moderate: 100, poor: 250, severe: 350 },
    no2: { good: 40, moderate: 80, poor: 180, severe: 280 },
    so2: { good: 40, moderate: 80, poor: 380, severe: 800 },
    co: { good: 1, moderate: 2, poor: 10, severe: 17 },
    o3: { good: 50, moderate: 100, poor: 168, severe: 208 }
  };
  return limits[pollutant] || {};
};

export const getPollutantCategory = (pollutant, value) => {
  const limits = getPollutantLimit(pollutant);
  if (value <= limits.good) return 'Good';
  if (value <= limits.moderate) return 'Moderate';
  if (value <= limits.poor) return 'Poor';
  return 'Severe';
};
