from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta
import random
import math

app = Flask(__name__)
app.secret_key = 'your-secure-secret-key-here'  # Replace with a secure, random key in production
app.config['SESSION_PERMANENT'] = False

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        c.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return User(user[0], user[1]) if user else None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Initialize SQLite database
def init_db():
    try:
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
        # Alerts table
        c.execute('''CREATE TABLE IF NOT EXISTS alerts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      type TEXT NOT NULL,
                      location TEXT NOT NULL,
                      magnitude REAL,
                      latitude REAL NOT NULL,
                      longitude REAL NOT NULL,
                      timestamp TEXT NOT NULL,
                      weather_condition TEXT NOT NULL)''')
        # Survival tips table
        c.execute('''CREATE TABLE IF NOT EXISTS survival_tips
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      disaster TEXT NOT NULL,
                      tips TEXT NOT NULL)''')
        # Guides table
        c.execute('''CREATE TABLE IF NOT EXISTS guides
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      disaster TEXT NOT NULL,
                      content TEXT NOT NULL)''')
        
        # Insert sample data if tables are empty
        c.execute('SELECT COUNT(*) FROM users')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                      ('admin', generate_password_hash('admin123')))
        
        c.execute('SELECT COUNT(*) FROM alerts')
        if c.fetchone()[0] == 0:
            sample_alerts = [
                ('Earthquake', 'Tamil Nadu, India', 5.5, 13.0827, 80.2707, datetime.now().isoformat(), 'Clear'),
                ('Cyclone', 'Odisha, India', 0.0, 20.2961, 86.6700, (datetime.now() - timedelta(hours=1)).isoformat(), 'Rainy'),
                ('Flood', 'Uttarakhand, India', 0.0, 30.3165, 78.0322, (datetime.now() - timedelta(hours=2)).isoformat(), 'Rainy')
            ]
            c.executemany('INSERT INTO alerts (type, location, magnitude, latitude, longitude, timestamp, weather_condition) VALUES (?, ?, ?, ?, ?, ?, ?)', sample_alerts)
        
        c.execute('SELECT COUNT(*) FROM survival_tips')
        if c.fetchone()[0] == 0:
            sample_tips = [
                ('Earthquake', 'Stay indoors. Drop, cover, and hold on. Avoid doorways.'),
                ('Cyclone', 'Evacuate if advised. Secure heavy objects. Stay away from windows.'),
                ('Flood', 'Move to higher ground. Avoid walking in floodwater. Turn off electricity.')
            ]
            c.executemany('INSERT INTO survival_tips (disaster, tips) VALUES (?, ?)', sample_tips)
        
        c.execute('SELECT COUNT(*) FROM guides')
        if c.fetchone()[0] == 0:
            sample_guides = [
                ('Earthquake', 'Prepare an emergency kit with food, water, and first-aid supplies. Identify safe spots in your home. Practice earthquake drills regularly.'),
                ('Cyclone', 'Know your evacuation routes. Keep your property clear of debris. Install storm shutters or board up windows before a cyclone hits.'),
                ('Flood', 'Elevate appliances above flood levels. Create a flood evacuation plan. Store important documents in waterproof containers.')
            ]
            c.executemany('INSERT INTO guides (disaster, content) VALUES (?, ?)', sample_guides)
        
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('login.html', error='Username and password are required')
        
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        c.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            login_user(User(user[0], user[1]))
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/tips')
@login_required
def tips():
    return render_template('tips.html')

@app.route('/guides')
@login_required
def guides():
    return render_template('guides.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# API endpoints
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    try:
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        c.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            login_user(User(user[0], user[1]))
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    try:
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                  (username, generate_password_hash(password)))
        conn.commit()
        c.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        login_user(User(user[0], user[1]))
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'}), 500
    finally:
        conn.close()

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    try:
        logout_user()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'}), 500

@app.route('/api/data', methods=['GET', 'POST'])
@login_required
def api_data():
    user_location = None
    if request.method == 'POST':
        data = request.get_json()
        user_location = {
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude')
        } if data.get('latitude') and data.get('longitude') else None

    try:
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        
        # Fetch alerts
        c.execute('SELECT type, location, magnitude, latitude, longitude, timestamp, weather_condition FROM alerts ORDER BY timestamp DESC LIMIT 10')
        alerts = [
            {
                'type': row[0],
                'location': row[1],
                'magnitude': row[2],
                'latitude': row[3],
                'longitude': row[4],
                'timestamp': row[5],
                'weather_condition': row[6]
            } for row in c.fetchall()
        ]
        
        # Fetch survival tips
        c.execute('SELECT disaster, tips FROM survival_tips')
        survival_tips = [
            {'disaster': row[0], 'tips': row[1].split('. ') if row[1] else []}
            for row in c.fetchall()
        ]
        
        # Fetch guides
        c.execute('SELECT disaster, content FROM guides')
        guides = [
            {'disaster': row[0], 'content': row[1]}
            for row in c.fetchall()
        ]
        
        conn.close()
        
        # Simulate real-time alert (for demo purposes)
        if random.random() < 0.2:  # 20% chance of new alert
            new_alert = {
                'type': random.choice(['Earthquake', 'Cyclone', 'Flood']),
                'location': random.choice(['Tamil Nadu, India', 'Odisha, India', 'Uttarakhand, India']),
                'magnitude': round(random.uniform(3.0, 7.0), 1) if random.random() > 0.5 else 0.0,
                'latitude': random.uniform(8, 35),
                'longitude': random.uniform(68, 97),
                'timestamp': datetime.now().isoformat(),
                'weather_condition': random.choice(['Clear', 'Rainy', 'Cloudy'])
            }
            conn = sqlite3.connect('alerts.db')
            c = conn.cursor()
            c.execute('INSERT INTO alerts (type, location, magnitude, latitude, longitude, timestamp, weather_condition) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (new_alert['type'], new_alert['location'], new_alert['magnitude'],
                       new_alert['latitude'], new_alert['longitude'], new_alert['timestamp'], new_alert['weather_condition']))
            conn.commit()
            conn.close()
            alerts.insert(0, new_alert)
        
        # Simulate weather data (mock)
        weather = {
            'location': user_location and 'Your Location' or 'India',
            'temperature': round(random.uniform(20, 35), 1),
            'condition': random.choice(['Clear', 'Rainy', 'Cloudy']),
            'updated': datetime.now().isoformat()
        }

        # Filter alerts based on weather condition
        if weather['condition'] == 'Rainy':
            alerts = [alert for alert in alerts if alert['type'] in ['Flood', 'Cyclone'] or random.random() < 0.3]
        
        return jsonify({
            'alerts': alerts,
            'weather': weather,
            'survival_tips': survival_tips,
            'guides': guides
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching data: {e}'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)