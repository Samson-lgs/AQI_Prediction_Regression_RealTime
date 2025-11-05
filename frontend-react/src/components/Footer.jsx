import React from 'react';
import { Github, Heart } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <p>
            Built with <Heart size={16} className="heart-icon" /> using Flask, PostgreSQL, and React
          </p>
          <div className="footer-links">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer">
              <Github size={20} />
              <span>View on GitHub</span>
            </a>
          </div>
        </div>
        <div className="footer-meta">
          <p>© 2024 AQI Prediction System. Real-time air quality monitoring and forecasting.</p>
        </div>
      </div>

      <style jsx>{`
        .footer {
          background: #1f2937;
          color: #e5e7eb;
          margin-top: auto;
          padding: 2rem 0;
        }

        .footer-container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 0 2rem;
        }

        .footer-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 1.5rem;
          border-bottom: 1px solid #374151;
        }

        .footer-content p {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin: 0;
        }

        .heart-icon {
          color: #ef4444;
        }

        .footer-links {
          display: flex;
          gap: 1.5rem;
        }

        .footer-links a {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #e5e7eb;
          text-decoration: none;
          transition: color 0.2s;
        }

        .footer-links a:hover {
          color: #3b82f6;
        }

        .footer-meta {
          padding-top: 1.5rem;
          text-align: center;
        }

        .footer-meta p {
          margin: 0;
          font-size: 0.875rem;
          color: #9ca3af;
        }

        @media (max-width: 768px) {
          .footer-content {
            flex-direction: column;
            gap: 1rem;
            text-align: center;
          }
        }
      `}</style>
    </footer>
  );
};

export default Footer;
