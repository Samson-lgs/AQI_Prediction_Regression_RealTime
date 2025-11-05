/**
 * Health advice and recommendations based on AQI levels
 */

export const AQI_CATEGORIES = {
  GOOD: { min: 0, max: 50, color: '#22c55e', label: 'Good' },
  MODERATE: { min: 51, max: 100, color: '#eab308', label: 'Moderate' },
  UNHEALTHY_SENSITIVE: { min: 101, max: 150, color: '#f97316', label: 'Unhealthy for Sensitive Groups' },
  UNHEALTHY: { min: 151, max: 200, color: '#ef4444', label: 'Unhealthy' },
  VERY_UNHEALTHY: { min: 201, max: 300, color: '#a855f7', label: 'Very Unhealthy' },
  HAZARDOUS: { min: 301, max: 500, color: '#7f1d1d', label: 'Hazardous' }
};

export function getAQICategory(aqi) {
  if (aqi == null) return null;
  
  for (const [key, category] of Object.entries(AQI_CATEGORIES)) {
    if (aqi >= category.min && aqi <= category.max) {
      return { ...category, key };
    }
  }
  
  if (aqi > 500) {
    return { ...AQI_CATEGORIES.HAZARDOUS, key: 'HAZARDOUS' };
  }
  
  return null;
}

export function getHealthAdvice(aqi) {
  const category = getAQICategory(aqi);
  if (!category) return null;

  const adviceMap = {
    GOOD: {
      general: 'Air quality is satisfactory, and air pollution poses little or no risk.',
      sensitive: 'It\'s a great day to be active outside!',
      outdoor: 'Perfect conditions for outdoor activities.',
      actions: [
        'Enjoy outdoor activities',
        'Open windows for fresh air',
        'Good time for exercise outdoors'
      ]
    },
    MODERATE: {
      general: 'Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.',
      sensitive: 'Unusually sensitive people should consider reducing prolonged or heavy outdoor exertion.',
      outdoor: 'Generally acceptable for outdoor activities.',
      actions: [
        'Sensitive individuals should watch for symptoms',
        'Consider reducing prolonged outdoor exertion if sensitive',
        'Monitor air quality if you have respiratory conditions'
      ]
    },
    UNHEALTHY_SENSITIVE: {
      general: 'Members of sensitive groups may experience health effects. The general public is less likely to be affected.',
      sensitive: 'People with respiratory or heart conditions, children, and older adults should reduce prolonged or heavy outdoor exertion.',
      outdoor: 'Limit prolonged outdoor activities if you\'re sensitive.',
      actions: [
        'Sensitive groups: reduce prolonged outdoor exertion',
        'Keep windows closed if air quality worsens',
        'Consider wearing a mask if you must go outside',
        'Use air purifiers indoors'
      ]
    },
    UNHEALTHY: {
      general: 'Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.',
      sensitive: 'People with respiratory or heart conditions, children, and older adults should avoid prolonged outdoor exertion.',
      outdoor: 'Everyone should reduce prolonged or heavy outdoor exertion.',
      actions: [
        'Avoid prolonged outdoor activities',
        'Keep windows closed',
        'Use air purifiers indoors',
        'Wear N95 masks if going outside',
        'Sensitive groups: stay indoors'
      ]
    },
    VERY_UNHEALTHY: {
      general: 'Health alert: The risk of health effects is increased for everyone.',
      sensitive: 'People with respiratory or heart conditions, children, and older adults should avoid all outdoor exertion.',
      outdoor: 'Everyone should avoid prolonged outdoor exertion.',
      actions: [
        'Stay indoors with windows closed',
        'Run air purifiers on high',
        'Wear N95/N99 masks if you must go outside',
        'Postpone outdoor activities',
        'Monitor symptoms and seek medical help if needed'
      ]
    },
    HAZARDOUS: {
      general: 'Health warning of emergency conditions: everyone is more likely to be affected.',
      sensitive: 'Everyone should avoid all outdoor exertion. Stay indoors and keep activity levels low.',
      outdoor: 'Remain indoors and keep activity levels low.',
      actions: [
        'STAY INDOORS - do not go outside',
        'Seal windows and doors',
        'Use air purifiers continuously',
        'Avoid all physical exertion',
        'Seek medical attention if experiencing symptoms',
        'Follow official health advisories'
      ]
    }
  };

  return {
    category: category.label,
    color: category.color,
    ...adviceMap[category.key]
  };
}

export function getProtectionLevel(aqi) {
  if (aqi == null) return 'unknown';
  if (aqi <= 50) return 'none';
  if (aqi <= 100) return 'minimal';
  if (aqi <= 150) return 'moderate';
  if (aqi <= 200) return 'high';
  if (aqi <= 300) return 'very-high';
  return 'extreme';
}

export function getMaskRecommendation(aqi) {
  if (aqi == null) return 'No mask needed';
  if (aqi <= 100) return 'No mask needed';
  if (aqi <= 150) return 'Consider mask for sensitive individuals';
  if (aqi <= 200) return 'N95 mask recommended for outdoor activities';
  if (aqi <= 300) return 'N95 mask required for any outdoor exposure';
  return 'N95/N99 mask essential - avoid going outside';
}
