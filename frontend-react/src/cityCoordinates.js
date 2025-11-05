// Minimal coordinates for supported Indian cities (subset; extend as needed)
export const CITY_COORDINATES = {
  Delhi: [28.7041, 77.1025],
  Mumbai: [19.0760, 72.8777],
  Bangalore: [12.9716, 77.5946],
  Chennai: [13.0827, 80.2707],
  Kolkata: [22.5726, 88.3639],
  Hyderabad: [17.3850, 78.4867],
  Pune: [18.5204, 73.8567],
  Ahmedabad: [23.0225, 72.5714],
  Jaipur: [26.9124, 75.7873],
  Lucknow: [26.8467, 80.9462],
  Kanpur: [26.4499, 80.3319],
  Nagpur: [21.1458, 79.0882],
  Indore: [22.7196, 75.8577],
  Thane: [19.2183, 72.9781],
  Bhopal: [23.2599, 77.4126],
  Visakhapatnam: [17.6869, 83.2185],
  PimpriChinchwad: [18.6298, 73.7997],
  Patna: [25.5941, 85.1376],
  Vadodara: [22.3072, 73.1812],
  Ghaziabad: [28.6692, 77.4538],
  Ludhiana: [30.9010, 75.8573],
  Agra: [27.1767, 78.0081],
  Nashik: [19.9975, 73.7898],
  Faridabad: [28.4089, 77.3178],
  Meerut: [28.9845, 77.7064],
  Rajkot: [22.3039, 70.8022],
  Varanasi: [25.3176, 82.9739],
  Srinagar: [34.0837, 74.7973],
  Aurangabad: [19.8762, 75.3433],
  Dhanbad: [23.7957, 86.4304],
  Amritsar: [31.6340, 74.8723],
  NaviMumbai: [19.0330, 73.0297],
  Allahabad: [25.4358, 81.8463],
  Ranchi: [23.3441, 85.3096],
  Howrah: [22.5958, 88.2636],
  Coimbatore: [11.0168, 76.9558],
  Jabalpur: [23.1815, 79.9864],
  Gwalior: [26.2183, 78.1828],
  Vijayawada: [16.5062, 80.6480],
  Jodhpur: [26.2389, 73.0243],
  Madurai: [9.9252, 78.1198],
  Raipur: [21.2514, 81.6296],
  Kota: [25.2138, 75.8648],
  Chandigarh: [30.7333, 76.7794],
  Guwahati: [26.1445, 91.7362],
  Solapur: [17.6599, 75.9064],
  Mysore: [12.2958, 76.6394],
  Gurugram: [28.4595, 77.0266],
  Aligarh: [27.8974, 78.0880],
  Jalandhar: [31.3260, 75.5762],
  Bhubaneswar: [20.2961, 85.8245],
  Salem: [11.6643, 78.1460],
  Warangal: [17.9689, 79.5941]
};

export function getAQIColor(aqi) {
  if (aqi == null) return '#9ca3af';
  if (aqi <= 50) return '#22c55e';
  if (aqi <= 100) return '#eab308';
  if (aqi <= 150) return '#f97316';
  if (aqi <= 200) return '#ef4444';
  if (aqi <= 300) return '#a855f7';
  return '#7f1d1d';
}
