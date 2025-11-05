import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useStore } from './store';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import Footer from './components/Footer';
import Rankings from './pages/Rankings.jsx';
import Compare from './pages/Compare.jsx';
import MapView from './pages/MapView.jsx';

function App() {
  const { connectWebSocket, disconnectWebSocket, fetchCities } = useStore();

  useEffect(() => {
    // Initialize WebSocket connection
    connectWebSocket();

    // Fetch initial cities list
    fetchCities();

    // Cleanup on unmount
    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket, fetchCities]);

  return (
    <Router>
      <div className="app">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/city/:cityId" element={<Dashboard />} />
            <Route path="/rankings" element={<Rankings />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/map" element={<MapView />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
