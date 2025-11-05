import React, { useState, useEffect } from 'react';
import { useStore } from '../store';
import axios from 'axios';
import { Bell, Plus, Trash2, Mail, AlertCircle, CheckCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const AlertsManagement = () => {
  const { cities, selectedCity } = useStore();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    city: selectedCity || '',
    threshold: 150,
    alert_type: 'email',
    contact: ''
  });

  // Fetch alerts for selected city
  const fetchAlerts = async (city) => {
    if (!city) return;
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/alerts/list/${city}`);
      setAlerts(response.data.alerts || []);
      setError(null);
    } catch (err) {
      setError('Failed to load alerts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (formData.city) {
      fetchAlerts(formData.city);
    }
  }, [formData.city]);

  // Create new alert
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.contact.trim()) {
      setError('Email address is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const response = await axios.post(`${API_BASE_URL}/alerts/create`, {
        city: formData.city,
        threshold: parseInt(formData.threshold),
        alert_type: formData.alert_type,
        contact: formData.contact.trim()
      });

      setSuccess(`Alert created successfully! ID: ${response.data.alert_id}`);
      
      // Reset form
      setFormData({
        ...formData,
        contact: ''
      });
      
      // Refresh alerts list
      fetchAlerts(formData.city);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create alert');
    } finally {
      setLoading(false);
    }
  };

  // Deactivate alert
  const handleDeactivate = async (alertId) => {
    if (!confirm('Are you sure you want to deactivate this alert?')) return;

    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/alerts/deactivate/${alertId}`);
      setSuccess('Alert deactivated successfully');
      fetchAlerts(formData.city);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to deactivate alert');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="alerts-page">
        <div className="page-header">
          <div className="header-content">
            <Bell size={32} />
            <div>
              <h1>AQI Alerts Management</h1>
              <p>Set up email notifications when AQI exceeds your threshold</p>
            </div>
          </div>
        </div>

        {/* Alert Messages */}
        {error && (
          <div className="alert alert-error">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}
        
        {success && (
          <div className="alert alert-success">
            <CheckCircle size={20} />
            <span>{success}</span>
          </div>
        )}

        <div className="alerts-grid">
          {/* Create Alert Form */}
          <div className="card">
            <div className="card-header">
              <h2><Plus size={20} /> Create New Alert</h2>
            </div>
            <div className="card-content">
              <form onSubmit={handleSubmit} className="alert-form">
                <div className="form-group">
                  <label htmlFor="city">City</label>
                  <select
                    id="city"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    required
                  >
                    <option value="">Select a city</option>
                    {cities.map(city => (
                      <option key={city.name} value={city.name}>{city.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="threshold">AQI Threshold</label>
                  <input
                    type="number"
                    id="threshold"
                    min="1"
                    max="500"
                    value={formData.threshold}
                    onChange={(e) => setFormData({ ...formData, threshold: e.target.value })}
                    required
                  />
                  <small>Alert when AQI exceeds this value</small>
                </div>

                <div className="form-group">
                  <label htmlFor="alert_type">Alert Type</label>
                  <select
                    id="alert_type"
                    value={formData.alert_type}
                    onChange={(e) => setFormData({ ...formData, alert_type: e.target.value })}
                    required
                  >
                    <option value="email">Email</option>
                    <option value="sms" disabled>SMS (Coming Soon)</option>
                    <option value="webhook" disabled>Webhook (Coming Soon)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="contact">Email Address</label>
                  <div className="input-with-icon">
                    <Mail size={18} />
                    <input
                      type="email"
                      id="contact"
                      placeholder="your.email@example.com"
                      value={formData.contact}
                      onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Alert'}
                </button>
              </form>
            </div>
          </div>

          {/* Active Alerts List */}
          <div className="card">
            <div className="card-header">
              <h2>Active Alerts {formData.city && `for ${formData.city}`}</h2>
            </div>
            <div className="card-content">
              {loading && !alerts.length ? (
                <div className="loading-state">Loading alerts...</div>
              ) : alerts.length === 0 ? (
                <div className="empty-state">
                  <Bell size={48} style={{ color: '#d1d5db' }} />
                  <p>No alerts configured yet</p>
                  <small>Create an alert to get notified when AQI exceeds your threshold</small>
                </div>
              ) : (
                <div className="alerts-list">
                  {alerts.map((alert) => (
                    <div key={alert.id} className={`alert-item ${!alert.active ? 'inactive' : ''}`}>
                      <div className="alert-info">
                        <div className="alert-main">
                          <strong>{alert.city}</strong>
                          <span className="threshold-badge">
                            Threshold: {alert.threshold} AQI
                          </span>
                        </div>
                        <div className="alert-details">
                          <span className="alert-type">{alert.alert_type}</span>
                          <span className="alert-contact">{alert.contact}</span>
                        </div>
                        {alert.last_notified && (
                          <div className="alert-meta">
                            Last notified: {new Date(alert.last_notified).toLocaleString()}
                          </div>
                        )}
                      </div>
                      {alert.active && (
                        <button
                          className="btn-icon-danger"
                          onClick={() => handleDeactivate(alert.id)}
                          title="Deactivate alert"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem;
        }

        .page-header {
          margin-bottom: 2rem;
        }

        .header-content {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .header-content h1 {
          margin: 0;
          font-size: 2rem;
          color: #1f2937;
        }

        .header-content p {
          margin: 0.25rem 0 0;
          color: #6b7280;
        }

        .alert {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          border-radius: 0.5rem;
          margin-bottom: 1rem;
        }

        .alert-error {
          background: #fef2f2;
          color: #991b1b;
          border: 1px solid #fecaca;
        }

        .alert-success {
          background: #f0fdf4;
          color: #166534;
          border: 1px solid #bbf7d0;
        }

        .alerts-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
        }

        .alert-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group label {
          font-weight: 500;
          color: #374151;
        }

        .form-group input,
        .form-group select {
          padding: 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.5rem;
          font-size: 1rem;
        }

        .form-group small {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .input-with-icon {
          position: relative;
          display: flex;
          align-items: center;
        }

        .input-with-icon svg {
          position: absolute;
          left: 0.75rem;
          color: #9ca3af;
        }

        .input-with-icon input {
          padding-left: 2.75rem;
          width: 100%;
        }

        .btn-primary {
          padding: 0.75rem 1.5rem;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 0.5rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-primary:hover:not(:disabled) {
          background: #2563eb;
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .loading-state {
          text-align: center;
          padding: 2rem;
          color: #6b7280;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 3rem;
          text-align: center;
        }

        .empty-state p {
          margin: 1rem 0 0.5rem;
          color: #6b7280;
          font-weight: 500;
        }

        .empty-state small {
          color: #9ca3af;
        }

        .alerts-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .alert-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          transition: all 0.2s;
        }

        .alert-item:hover {
          border-color: #3b82f6;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .alert-item.inactive {
          opacity: 0.6;
          background: #f9fafb;
        }

        .alert-info {
          flex: 1;
        }

        .alert-main {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.5rem;
        }

        .threshold-badge {
          padding: 0.25rem 0.75rem;
          background: #eff6ff;
          color: #1e40af;
          border-radius: 9999px;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .alert-details {
          display: flex;
          gap: 1rem;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .alert-type {
          text-transform: capitalize;
        }

        .alert-meta {
          margin-top: 0.5rem;
          font-size: 0.75rem;
          color: #9ca3af;
        }

        .btn-icon-danger {
          padding: 0.5rem;
          background: #fef2f2;
          color: #dc2626;
          border: 1px solid #fecaca;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-icon-danger:hover {
          background: #fee2e2;
          border-color: #fca5a5;
        }

        @media (max-width: 1024px) {
          .alerts-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 768px) {
          .container {
            padding: 1rem;
          }

          .header-content {
            flex-direction: column;
            align-items: flex-start;
          }

          .header-content h1 {
            font-size: 1.5rem;
          }
        }
      `}</style>
    </div>
  );
};

export default AlertsManagement;
