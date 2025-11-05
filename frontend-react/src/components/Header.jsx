import React from 'react';
import { Menu, X, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStore } from '../store';

const Header = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const { connected } = useStore();

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="header-brand">
          <Activity size={28} />
          <span>AQI Prediction System</span>
        </Link>

        <nav className={`header-nav ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          <Link to="/" onClick={() => setMobileMenuOpen(false)}>Dashboard</Link>
          <Link to="/rankings" onClick={() => setMobileMenuOpen(false)}>Rankings</Link>
          <Link to="/compare" onClick={() => setMobileMenuOpen(false)}>Compare</Link>
        </nav>

        <div className="header-status">
          <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {connected ? 'Live' : 'Offline'}
          </div>
          
          <button 
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      <style jsx>{`
        .header {
          background: white;
          border-bottom: 1px solid #e5e7eb;
          position: sticky;
          top: 0;
          z-index: 100;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .header-container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 1rem 2rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .header-brand {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 1.25rem;
          font-weight: 600;
          color: #1f2937;
          text-decoration: none;
        }

        .header-nav {
          display: flex;
          gap: 2rem;
        }

        .header-nav a {
          color: #6b7280;
          text-decoration: none;
          font-weight: 500;
          transition: color 0.2s;
        }

        .header-nav a:hover {
          color: #3b82f6;
        }

        .header-status {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          animation: pulse 2s infinite;
        }

        .connected .status-dot {
          background: #10b981;
        }

        .disconnected .status-dot {
          background: #ef4444;
          animation: none;
        }

        .mobile-menu-toggle {
          display: none;
          background: none;
          border: none;
          cursor: pointer;
          color: #6b7280;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        @media (max-width: 768px) {
          .header-nav {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            flex-direction: column;
            padding: 1rem 2rem;
            border-bottom: 1px solid #e5e7eb;
            display: none;
            gap: 1rem;
          }

          .header-nav.mobile-open {
            display: flex;
          }

          .mobile-menu-toggle {
            display: block;
          }
        }
      `}</style>
    </header>
  );
};

export default Header;
