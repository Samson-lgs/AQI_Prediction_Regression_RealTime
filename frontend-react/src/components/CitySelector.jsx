import React, { useState, useEffect, useRef } from 'react';
import { useStore } from '../store';
import { Search, MapPin, ChevronDown } from 'lucide-react';

const CitySelector = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);
  
  const { cities, selectedCity, setSelectedCity, subscribeToCity, unsubscribeFromCity } = useStore();

  // Ensure cities is always an array
  const citiesArray = Array.isArray(cities) ? cities : [];
  
  const filteredCities = citiesArray.filter(city =>
    city.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleCitySelect = (city) => {
    if (selectedCity) {
      unsubscribeFromCity(selectedCity);
    }
    setSelectedCity(city.name);
    subscribeToCity(city.name);
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className="city-selector" ref={dropdownRef}>
      <button 
        className="selector-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        <MapPin size={20} />
        <span>{selectedCity || 'Select a city'}</span>
        <ChevronDown size={20} className={`chevron ${isOpen ? 'open' : ''}`} />
      </button>

      {isOpen && (
        <div className="dropdown">
          <div className="search-box">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search cities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>

          <div className="cities-list">
            {filteredCities.length > 0 ? (
              filteredCities.map(city => (
                <button
                  key={city.id || city.name}
                  className={`city-item ${selectedCity === city.name ? 'selected' : ''}`}
                  onClick={() => handleCitySelect(city)}
                >
                  <MapPin size={16} />
                  <span>{city.name}</span>
                  {city.state && <span className="city-state">{city.state}</span>}
                </button>
              ))
            ) : (
              <div className="no-results">No cities found</div>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        .city-selector {
          position: relative;
          width: 300px;
        }

        .selector-button {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1rem;
          background: white;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 1rem;
        }

        .selector-button:hover {
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .selector-button span {
          flex: 1;
          text-align: left;
          color: #1f2937;
        }

        .chevron {
          transition: transform 0.2s;
          color: #6b7280;
        }

        .chevron.open {
          transform: rotate(180deg);
        }

        .dropdown {
          position: absolute;
          top: calc(100% + 0.5rem);
          left: 0;
          right: 0;
          background: white;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
          z-index: 1000;
          max-height: 400px;
          display: flex;
          flex-direction: column;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          border-bottom: 1px solid #e5e7eb;
          color: #6b7280;
        }

        .search-box input {
          flex: 1;
          border: none;
          outline: none;
          font-size: 0.875rem;
          color: #1f2937;
        }

        .cities-list {
          overflow-y: auto;
          max-height: 320px;
        }

        .city-item {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1rem;
          border: none;
          background: none;
          cursor: pointer;
          transition: background 0.2s;
          text-align: left;
          color: #1f2937;
        }

        .city-item:hover {
          background: #f3f4f6;
        }

        .city-item.selected {
          background: #eff6ff;
          color: #3b82f6;
        }

        .city-state {
          margin-left: auto;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .no-results {
          padding: 2rem;
          text-align: center;
          color: #6b7280;
        }

        @media (max-width: 768px) {
          .city-selector {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default CitySelector;
