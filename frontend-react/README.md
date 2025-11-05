# AQI Prediction System - React Frontend

Modern, real-time air quality monitoring dashboard built with React, Vite, and Socket.IO.

## Features

- 🎯 **Real-time Updates**: WebSocket integration for live AQI data
- 📊 **Interactive Charts**: Forecast and historical data visualization with Recharts
- 🏙️ **56 Cities**: Comprehensive coverage of Indian cities
- 🎨 **Modern UI**: Clean, responsive design with CSS-in-JS
- 📱 **Mobile Responsive**: Works seamlessly on all devices
- 🔄 **State Management**: Efficient state handling with Zustand
- ⚡ **Fast Development**: Vite for instant HMR and build

## Tech Stack

- **React 18.2** - UI framework
- **Vite 5.0** - Build tool and dev server
- **Zustand 4.4** - State management
- **Socket.IO Client 4.7** - WebSocket communication
- **Recharts 2.10** - Data visualization
- **React Router 6.20** - Routing
- **Axios 1.6** - HTTP client
- **Lucide React** - Icon library

## Project Structure

```
frontend-react/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── Dashboard.jsx        # Main dashboard layout
│   │   ├── Header.jsx           # App header with navigation
│   │   ├── Footer.jsx           # App footer
│   │   ├── CitySelector.jsx    # City dropdown with search
│   │   ├── AQICard.jsx          # Current AQI display card
│   │   ├── ForecastChart.jsx   # 48-hour forecast chart
│   │   ├── HistoricalChart.jsx # 24-hour historical chart
│   │   ├── PollutantMetrics.jsx # Pollutant level cards
│   │   └── ModelMetrics.jsx     # Model performance display
│   ├── store.js         # Zustand state management
│   ├── utils.js         # Utility functions (AQI helpers)
│   ├── App.jsx          # Main App component
│   ├── main.jsx         # React entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
└── package.json         # Dependencies

```

## Installation

### Prerequisites

- Node.js 18+ and npm
- Backend Flask server running on `http://localhost:5000`

### Setup

1. Navigate to frontend directory:
```powershell
cd frontend-react
```

2. Install dependencies:
```powershell
npm install
```

3. Start development server:
```powershell
npm run dev
```

The app will be available at `http://localhost:3000`

## Available Scripts

```powershell
# Development server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Configuration

### API Proxy

The Vite dev server proxies API requests to the Flask backend. Configuration in `vite.config.js`:

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/socket.io': 'http://localhost:5000'
    }
  }
})
```

### Environment Variables

Create a `.env` file for custom configuration:

```env
VITE_API_URL=http://localhost:5000
VITE_WS_URL=http://localhost:5000
```

## Components Overview

### Dashboard
Main view that displays:
- Current AQI with trend indicator
- 6 pollutant metrics (PM2.5, PM10, NO₂, SO₂, CO, O₃)
- 48-hour forecast chart with confidence intervals
- 24-hour historical trend
- Model performance metrics

### CitySelector
Dropdown with search functionality:
- Filters 56 cities by name
- Shows current selection
- Subscribes to city-specific WebSocket updates

### AQICard
Large card showing:
- Current AQI value
- AQI category (Good/Satisfactory/Moderate/Poor/Very Poor/Severe)
- Color-coded indicator
- Trend from previous hour
- Health description
- Last update timestamp

### ForecastChart
Interactive line chart with:
- 48-hour AQI predictions
- Confidence interval bands
- AQI category reference lines
- Hover tooltips with details
- Summary statistics

### PollutantMetrics
Grid of pollutant cards showing:
- Current pollutant levels
- Visual progress bars
- Category indicators
- Color-coded by severity

### ModelMetrics
Model performance display:
- R² Score, RMSE, MAE, MAPE for each model
- Best model highlighting
- Gradient background design

## State Management

Zustand store (`store.js`) manages:

### State
- `cities` - List of all cities
- `selectedCity` - Currently selected city
- `currentAQI` - Latest AQI data
- `forecast` - 48-hour predictions
- `historicalData` - Past 24 hours
- `modelMetrics` - Model performance
- `loading` - Loading state
- `error` - Error messages
- `connected` - WebSocket connection status

### Actions
- `fetchCities()` - Load cities list
- `fetchCurrentAQI(city)` - Get latest AQI
- `fetchForecast(city)` - Get predictions
- `fetchHistoricalData(city)` - Get past data
- `fetchModelMetrics(city)` - Get model performance
- `loadCityData(city)` - Composite action to load all data
- `connectWebSocket()` - Initialize WebSocket
- `subscribeToCity(city)` - Subscribe to city updates
- `unsubscribeFromCity(city)` - Unsubscribe from updates

## Styling

### AQI Color Scheme
- **Good (0-50)**: #00e400 (Green)
- **Satisfactory (51-100)**: #ffff00 (Yellow)
- **Moderate (101-200)**: #ff7e00 (Orange)
- **Poor (201-300)**: #ff0000 (Red)
- **Very Poor (301-400)**: #8f3f97 (Purple)
- **Severe (401+)**: #7e0023 (Maroon)

### Utility Classes
- `.card` - Standard card container
- `.button` - Button styles
- `.badge` - Status badges
- `.spinner` - Loading spinner
- `.grid` - Responsive grid layout

### Responsive Breakpoints
- Desktop: 1024px+
- Tablet: 768px - 1023px
- Mobile: < 768px

## WebSocket Integration

The app uses Socket.IO for real-time updates:

```javascript
// Connect on mount
useEffect(() => {
  connectWebSocket();
  return () => disconnectWebSocket();
}, []);

// Subscribe to city
subscribeToCity('Delhi');

// Handle updates
socket.on('aqi_update', (data) => {
  // Update state with new AQI data
});
```

### WebSocket Events

**Client → Server**:
- `connect` - Initial connection
- `subscribe_city` - Subscribe to city updates
- `unsubscribe_city` - Unsubscribe from city

**Server → Client**:
- `connection_response` - Connection confirmation
- `aqi_update` - New AQI data
- `prediction_update` - New forecast
- `aqi_alert` - AQI threshold alert

## API Integration

All API calls are handled through Axios in the Zustand store:

```javascript
// Example: Fetch current AQI
const response = await axios.get(`/api/v1/aqi/current/${city}`);
```

### API Endpoints Used
- `GET /api/v1/cities/` - List all cities
- `GET /api/v1/aqi/current/{city}` - Current AQI
- `GET /api/v1/forecast/{city}` - 48-hour forecast
- `GET /api/v1/aqi/history/{city}` - Historical data
- `GET /api/v1/models/performance/{city}` - Model metrics

## Production Build

Build optimized production bundle:

```powershell
npm run build
```

Output goes to `dist/` directory:
- Minified JavaScript
- Optimized CSS
- Code splitting
- Asset optimization

### Deployment

Deploy the `dist/` folder to any static hosting:
- Netlify
- Vercel
- GitHub Pages
- AWS S3 + CloudFront
- Azure Static Web Apps

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Development Tips

### Hot Module Replacement
Vite provides instant HMR. Changes reflect immediately without full reload.

### Component Development
Each component is self-contained with inline styles for easier maintenance.

### Debugging WebSocket
Check browser console for WebSocket connection status:
```javascript
console.log('WebSocket connected:', socket.connected);
```

### API Error Handling
Errors are caught and displayed in the UI. Check the error state:
```javascript
const { error } = useStore();
if (error) {
  // Display error message
}
```

## Performance Optimizations

- **Code Splitting**: React Router lazy loading
- **Memoization**: React.memo for expensive components
- **Virtual Scrolling**: For large city lists
- **Debounced Search**: City selector search
- **Lazy Loading**: Charts load on demand
- **WebSocket Reconnection**: Automatic retry on disconnect

## Troubleshooting

### WebSocket Connection Issues
- Ensure Flask backend is running
- Check proxy configuration in `vite.config.js`
- Verify CORS settings on backend

### API Errors
- Check Flask backend logs
- Verify API endpoints match backend routes
- Check network tab in browser DevTools

### Styling Issues
- Clear browser cache
- Check for CSS conflicts
- Verify custom properties are defined

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

MIT License - see LICENSE file for details

---

**Built with ❤️ using React, Vite, and modern web technologies**
