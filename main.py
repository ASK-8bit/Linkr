# main.py
import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates')

DATABASE = 'locations.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT NOT NULL,
                user_id TEXT UNIQUE
            )
        ''')
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        db.commit()
        db.close()

# Initialize the database when the app starts
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    hashed_password = generate_password_hash(password)

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        db.commit()
        user_id = cursor.lastrowid
        db.close()
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/submit-location', methods=['POST'])
def submit_location():
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
