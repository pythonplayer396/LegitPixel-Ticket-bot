
from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import logging
from datetime import datetime
from bson import ObjectId
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# MongoDB connection
MONGODB_URI = "mongodb+srv://rian3030:rian3030discord@cluster0.waoadym.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGODB_URI)
db = client['fakepixel_bot']
transcripts_collection = db['transcripts']
users_collection = db['users']

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        db.command('ping')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/transcripts', methods=['POST'])
def save_transcript():
    """Save a ticket transcript to MongoDB"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['ticket_number', 'user_id', 'category', 'messages']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create transcript document
        transcript = {
            "ticket_number": data['ticket_number'],
            "user_id": str(data['user_id']),
            "category": data['category'],
            "status": data.get('status', 'Closed'),
            "created_at": data.get('created_at', datetime.utcnow().isoformat()),
            "closed_at": data.get('closed_at', datetime.utcnow().isoformat()),
            "closed_by": data.get('closed_by', 'Unknown'),
            "closing_reason": data.get('closing_reason', 'No reason provided'),
            "messages": data['messages'],
            "details": data.get('details', ''),
            "claimed_by": data.get('claimed_by', 'Unclaimed'),
            "saved_at": datetime.utcnow().isoformat()
        }
        
        # Insert transcript
        result = transcripts_collection.insert_one(transcript)
        
        # Update user's transcript count
        users_collection.update_one(
            {"user_id": str(data['user_id'])},
            {
                "$inc": {"transcript_count": 1},
                "$set": {"last_ticket_date": datetime.utcnow().isoformat()}
            },
            upsert=True
        )
        
        logger.info(f"Saved transcript for ticket {data['ticket_number']} - User {data['user_id']}")
        
        return jsonify({
            "success": True,
            "transcript_id": str(result.inserted_id),
            "message": "Transcript saved successfully"
        }), 201
        
    except Exception as e:
        logger.error(f"Error saving transcript: {e}")
        return jsonify({"error": "Failed to save transcript"}), 500

@app.route('/api/transcripts/<user_id>', methods=['GET'])
def get_user_transcripts(user_id):
    """Get all transcripts for a specific user"""
    try:
        transcripts = list(transcripts_collection.find(
            {"user_id": str(user_id)},
            {"_id": 1, "ticket_number": 1, "category": 1, "status": 1, 
             "created_at": 1, "closed_at": 1, "closing_reason": 1}
        ).sort("closed_at", -1))
        
        # Convert ObjectId to string for JSON serialization
        for transcript in transcripts:
            transcript['_id'] = str(transcript['_id'])
        
        return jsonify({
            "success": True,
            "transcripts": transcripts,
            "count": len(transcripts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user transcripts: {e}")
        return jsonify({"error": "Failed to retrieve transcripts"}), 500

@app.route('/api/transcript/<ticket_number>/<user_id>', methods=['GET'])
def get_transcript_details(ticket_number, user_id):
    """Get detailed transcript for a specific ticket"""
    try:
        transcript = transcripts_collection.find_one({
            "ticket_number": ticket_number,
            "user_id": str(user_id)
        })
        
        if not transcript:
            return jsonify({"error": "Transcript not found or access denied"}), 404
        
        # Convert ObjectId to string
        transcript['_id'] = str(transcript['_id'])
        
        return jsonify({
            "success": True,
            "transcript": transcript
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting transcript details: {e}")
        return jsonify({"error": "Failed to retrieve transcript"}), 500

@app.route('/api/users/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Get user statistics"""
    try:
        user_data = users_collection.find_one({"user_id": str(user_id)})
        transcript_count = transcripts_collection.count_documents({"user_id": str(user_id)})
        
        stats = {
            "user_id": str(user_id),
            "total_tickets": transcript_count,
            "transcript_count": user_data.get('transcript_count', 0) if user_data else 0,
            "last_ticket_date": user_data.get('last_ticket_date') if user_data else None,
            "member_since": user_data.get('member_since', datetime.utcnow().isoformat()) if user_data else datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({"error": "Failed to retrieve user stats"}), 500

@app.route('/api/transcripts/search', methods=['GET'])
def search_transcripts():
    """Search transcripts by various criteria"""
    try:
        user_id = request.args.get('user_id')
        category = request.args.get('category')
        ticket_number = request.args.get('ticket_number')
        
        query = {}
        if user_id:
            query['user_id'] = str(user_id)
        if category:
            query['category'] = category
        if ticket_number:
            query['ticket_number'] = ticket_number
        
        transcripts = list(transcripts_collection.find(
            query,
            {"_id": 1, "ticket_number": 1, "category": 1, "status": 1, 
             "created_at": 1, "closed_at": 1, "user_id": 1}
        ).sort("closed_at", -1).limit(50))
        
        # Convert ObjectId to string
        for transcript in transcripts:
            transcript['_id'] = str(transcript['_id'])
        
        return jsonify({
            "success": True,
            "transcripts": transcripts,
            "count": len(transcripts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching transcripts: {e}")
        return jsonify({"error": "Failed to search transcripts"}), 500

@app.route('/api/transcripts/stats', methods=['GET'])
def get_transcript_stats():
    """Get overall transcript statistics"""
    try:
        total_transcripts = transcripts_collection.count_documents({})
        total_users = users_collection.count_documents({})
        
        # Get category breakdown
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = list(transcripts_collection.aggregate(category_pipeline))
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow().replace(day=datetime.utcnow().day-30).isoformat()
        recent_count = transcripts_collection.count_documents({
            "closed_at": {"$gte": thirty_days_ago}
        })
        
        stats = {
            "total_transcripts": total_transcripts,
            "total_users": total_users,
            "recent_activity": recent_count,
            "categories": categories
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting transcript stats: {e}")
        return jsonify({"error": "Failed to retrieve stats"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
