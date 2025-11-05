"""
WebSocket Handler for Real-time AQI Updates
Implements Flask-SocketIO for live data streaming
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize SocketIO (will be attached to Flask app)
socketio = None

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=True
    )
    
    logger.info("SocketIO initialized successfully")
    return socketio

# ============================================================================
# WebSocket Event Handlers
# ============================================================================

def register_socketio_events(socketio_instance):
    """Register all WebSocket event handlers"""
    global socketio
    socketio = socketio_instance
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid if 'request' in dir() else 'unknown'}")
        emit('connection_response', {
            'status': 'connected',
            'message': 'Connected to AQI real-time updates',
            'timestamp': datetime.now().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid if 'request' in dir() else 'unknown'}")
    
    @socketio.on('subscribe_city')
    def handle_subscribe_city(data):
        """Subscribe to updates for a specific city"""
        try:
            city = data.get('city')
            if not city:
                emit('error', {'message': 'City name is required'})
                return
            
            # Join room for this city
            room_name = f"city_{city}"
            join_room(room_name)
            
            logger.info(f"Client subscribed to {city}")
            
            emit('subscription_confirmed', {
                'city': city,
                'message': f'Subscribed to {city} updates',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error subscribing to city: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('unsubscribe_city')
    def handle_unsubscribe_city(data):
        """Unsubscribe from city updates"""
        try:
            city = data.get('city')
            if not city:
                emit('error', {'message': 'City name is required'})
                return
            
            # Leave room for this city
            room_name = f"city_{city}"
            leave_room(room_name)
            
            logger.info(f"Client unsubscribed from {city}")
            
            emit('unsubscription_confirmed', {
                'city': city,
                'message': f'Unsubscribed from {city} updates',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error unsubscribing from city: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('subscribe_all')
    def handle_subscribe_all():
        """Subscribe to updates for all cities"""
        try:
            join_room('all_cities')
            
            logger.info("Client subscribed to all cities")
            
            emit('subscription_confirmed', {
                'scope': 'all_cities',
                'message': 'Subscribed to all cities updates',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error subscribing to all cities: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('request_current_aqi')
    def handle_request_current_aqi(data):
        """Request current AQI for a city"""
        try:
            city = data.get('city')
            if not city:
                emit('error', {'message': 'City name is required'})
                return
            
            from database.db_operations import DatabaseOperations
            from datetime import timedelta
            
            db = DatabaseOperations()
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=1)
            
            aqi_data = db.get_pollution_data(city, start_date, end_date)
            
            if aqi_data:
                latest = aqi_data[0]
                emit('current_aqi', {
                    'city': city,
                    'aqi': latest['aqi_value'],
                    'pm25': latest['pm25'],
                    'pm10': latest['pm10'],
                    'timestamp': str(latest['timestamp'])
                })
            else:
                emit('error', {'message': f'No data available for {city}'})
                
        except Exception as e:
            logger.error(f"Error fetching current AQI: {str(e)}")
            emit('error', {'message': str(e)})
    
    logger.info("SocketIO event handlers registered")

# ============================================================================
# Broadcast Functions (called by backend services)
# ============================================================================

def broadcast_aqi_update(city, aqi_data):
    """Broadcast AQI update to all subscribed clients"""
    if not socketio:
        logger.warning("SocketIO not initialized")
        return
    
    try:
        room_name = f"city_{city}"
        
        socketio.emit('aqi_update', {
            'city': city,
            'aqi': aqi_data.get('aqi_value'),
            'pm25': aqi_data.get('pm25'),
            'pm10': aqi_data.get('pm10'),
            'no2': aqi_data.get('no2'),
            'so2': aqi_data.get('so2'),
            'co': aqi_data.get('co'),
            'o3': aqi_data.get('o3'),
            'timestamp': str(aqi_data.get('timestamp', datetime.now()))
        }, room=room_name)
        
        # Also broadcast to all_cities room
        socketio.emit('aqi_update', {
            'city': city,
            'aqi': aqi_data.get('aqi_value'),
            'timestamp': str(aqi_data.get('timestamp', datetime.now()))
        }, room='all_cities')
        
        logger.info(f"Broadcasted AQI update for {city}")
        
    except Exception as e:
        logger.error(f"Error broadcasting AQI update: {str(e)}")

def broadcast_prediction_update(city, prediction):
    """Broadcast new prediction to subscribed clients"""
    if not socketio:
        logger.warning("SocketIO not initialized")
        return
    
    try:
        room_name = f"city_{city}"
        
        socketio.emit('prediction_update', {
            'city': city,
            'predicted_aqi': prediction.get('predicted_aqi'),
            'confidence': prediction.get('confidence'),
            'forecast_timestamp': str(prediction.get('forecast_timestamp')),
            'model_used': prediction.get('model_used'),
            'timestamp': datetime.now().isoformat()
        }, room=room_name)
        
        logger.info(f"Broadcasted prediction update for {city}")
        
    except Exception as e:
        logger.error(f"Error broadcasting prediction: {str(e)}")

def broadcast_alert(city, alert_data):
    """Broadcast AQI alert to subscribed clients"""
    if not socketio:
        logger.warning("SocketIO not initialized")
        return
    
    try:
        room_name = f"city_{city}"
        
        socketio.emit('aqi_alert', {
            'city': city,
            'alert_type': alert_data.get('alert_type'),
            'current_aqi': alert_data.get('current_aqi'),
            'threshold': alert_data.get('threshold'),
            'message': alert_data.get('message'),
            'severity': alert_data.get('severity'),
            'timestamp': datetime.now().isoformat()
        }, room=room_name)
        
        # Also broadcast to all_cities room
        socketio.emit('aqi_alert', {
            'city': city,
            'alert_type': alert_data.get('alert_type'),
            'current_aqi': alert_data.get('current_aqi'),
            'severity': alert_data.get('severity'),
            'timestamp': datetime.now().isoformat()
        }, room='all_cities')
        
        logger.info(f"Broadcasted alert for {city}")
        
    except Exception as e:
        logger.error(f"Error broadcasting alert: {str(e)}")

def broadcast_system_status(status_data):
    """Broadcast system status update to all clients"""
    if not socketio:
        logger.warning("SocketIO not initialized")
        return
    
    try:
        socketio.emit('system_status', {
            'status': status_data.get('status'),
            'message': status_data.get('message'),
            'details': status_data.get('details'),
            'timestamp': datetime.now().isoformat()
        }, broadcast=True)
        
        logger.info("Broadcasted system status update")
        
    except Exception as e:
        logger.error(f"Error broadcasting system status: {str(e)}")

# ============================================================================
# Background Tasks
# ============================================================================

def start_background_tasks():
    """Start background tasks for periodic updates"""
    if not socketio:
        logger.warning("SocketIO not initialized")
        return
    
    @socketio.on('start_live_updates')
    def handle_start_live_updates():
        """Start periodic live updates for connected client"""
        # This would integrate with the scheduler to push updates
        emit('live_updates_started', {
            'status': 'started',
            'interval': '5 minutes',
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info("Live updates started for client")
    
    logger.info("Background task handlers registered")
