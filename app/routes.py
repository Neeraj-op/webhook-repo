"""
Flask routes for webhook receiver and API endpoints
"""

from flask import Blueprint, request, jsonify, render_template
from app.extensions import get_db
from app.utils import parse_push_event, parse_pull_request_event, format_event_message
from datetime import datetime
import traceback

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render dashboard page"""
    return render_template('index.html')

@main_bp.route('/webhook/receiver', methods=['POST'])
def webhook_receiver():
    """
    Receive GitHub webhook events
    
    Accepts: Push, Pull Request, and Merge events
    Stores parsed data to MongoDB
    """
    try:
        payload = request.json
        
        if not payload:
            return jsonify({'error': 'No payload received'}), 400
        
        event_type = request.headers.get('X-GitHub-Event', '')
        
        print(f"📨 Received webhook: {event_type}")
        
        event_data = None
        
        if event_type == 'push':
            event_data = parse_push_event(payload)
        
        elif event_type == 'pull_request':
            event_data = parse_pull_request_event(payload)
        
        else:
            print(f"⚠️ Unsupported event type: {event_type}")
            return jsonify({
                'message': 'Event received but not processed',
                'event_type': event_type
            }), 200
        
        # Store in MongoDB
        if event_data:
            db = get_db()
            
            try:
                # Insert or update event (upsert based on request_id)
                result = db.events.update_one(
                    {'request_id': event_data['request_id']},
                    {'$set': event_data},
                    upsert=True
                )
                
                if result.upserted_id:
                    print(f"✅ New event stored: {event_data['action']} by {event_data['author']}")
                else:
                    print(f"ℹ️ Event updated: {event_data['action']} by {event_data['author']}")
                
                return jsonify({
                    'message': 'Event processed successfully',
                    'action': event_data['action'],
                    'author': event_data['author']
                }), 200
                
            except Exception as db_error:
                print(f"❌ Database error: {db_error}")
                traceback.print_exc()
                return jsonify({'error': 'Database error'}), 500
        
        return jsonify({'message': 'No data to process'}), 200
        
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/events', methods=['GET'])
def get_events():
    """
    Get all events from MongoDB
    
    Returns:
        JSON array of formatted events
    """
    try:
        db = get_db()
        
        # Get all events, sorted by timestamp (newest first)
        events = list(db.events.find().sort('_id', -1))
        
        # Format events for display
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': str(event.get('_id', '')),
                'message': format_event_message(event),
                'action': event.get('action', ''),
                'author': event.get('author', ''),
                'timestamp': event.get('timestamp', ''),
                'raw': {
                    'from_branch': event.get('from_branch'),
                    'to_branch': event.get('to_branch'),
                }
            })
        
        return jsonify(formatted_events), 200
        
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/events/clear', methods=['POST'])
def clear_events():
    """
    Clear all events from MongoDB
    """
    try:
        db = get_db()
        result = db.events.delete_many({})
        
        return jsonify({
            'message': 'Events cleared',
            'deleted_count': result.deleted_count
        }), 200
        
    except Exception as e:
        print(f"❌ Error clearing events: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        # Test database connection
        db.events.count_documents({})
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500