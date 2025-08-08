# main.py
import os
import sqlite3
from flask import Flask, request, jsonify, render_template
# Removed Flask-CORS import as it's no longer needed for same-origin hosting

app = Flask(__name__, template_folder='templates')

# Removed explicit CORS configuration as it's no longer needed
# CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

DATABASE = 'locations.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Ensure user_id is UNIQUE for INSERT OR REPLACE to work correctly
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT NOT NULL,
                user_id TEXT UNIQUE
            )
        ''')
        db.commit()
        db.close()

# Initialize the database when the app starts
init_db()

# This route will now serve the index.html from the templates folder
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit-location', methods=['POST'])
def submit_location():
    # Removed OPTIONS method and preflight handling as CORS is no longer an issue
    data = request.json
    if not data or 'latitude' not in data or 'longitude' not in data or 'user_id' not in data:
        return jsonify({"error": "Invalid data: missing latitude, longitude, or user_id"}), 400

    latitude = data['latitude']
    longitude = data['longitude']
    timestamp = data.get('timestamp', os.getenv('REPL_ID', 'unknown') + '_' + str(os.getpid()))
    user_id = data['user_id'] # user_id is now mandatory

    try:
        db = get_db()
        cursor = db.cursor()
        # Use INSERT OR REPLACE to update if user_id exists, otherwise insert
        cursor.execute(
            "INSERT OR REPLACE INTO locations (user_id, latitude, longitude, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, latitude, longitude, timestamp)
        )
        db.commit()
        db.close()
        print(f"Received and stored/updated location for user: {{user_id}} at {{latitude}}, {{longitude}}")
        return jsonify({"message": "Location received and stored/updated", "location": {"latitude": latitude, "longitude": longitude, "timestamp": timestamp, "user_id": user_id}}), 200
    except Exception as e:
        print(f"Error storing/updating location: {e}")
        return jsonify({"error": "Failed to store/update location", "details": str(e)}), 500

@app.route('/get-locations', methods=['GET'])
def get_locations():
    # Removed OPTIONS method and preflight handling as CORS is no longer an issue
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT latitude, longitude, timestamp, user_id FROM locations")
        locations = cursor.fetchall()
        db.close()
        # Convert Row objects to dictionaries for jsonify
        locations_list = [{k: item[k] for k in item.keys()} for item in locations]
        print(f"Fetched {len(locations_list)} locations.")
        return jsonify(locations_list), 200
    except Exception as e:
        print(f"Error fetching locations: {e}")
        return jsonify({"error": "Failed to fetch locations", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)