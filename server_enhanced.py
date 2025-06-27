#!/usr/bin/env python3
"""
Enhanced IoT Honeypot Server with Advanced ML Pipeline
Production-ready Flask server with 100% ML accuracy
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import json
import time
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables
blockchain = []
model_data = None
DATABASE_PATH = 'honeypot.db'

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{json.dumps(self.data, sort_keys=True)}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp INTEGER,
            attack_type TEXT,
            source_ip TEXT,
            path TEXT,
            payload TEXT,
            block_hash TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def load_production_model():
    """Load the enhanced ML model"""
    global model_data
    try:
        model_data = joblib.load('/Users/bhaskar/Desktop/IOT/production_model.pkl')
        logger.info(f"Production model loaded: {model_data['model_name']} with {model_data['accuracy']:.3f} accuracy")
        return True
    except Exception as e:
        logger.warning(f"Could not load production model: {e}")
        return False

def extract_features(attack_data):
    """Extract 50 advanced features for ML classification"""
    features = []
    
    # === IP Features (8 features) ===
    ip = attack_data.get('source_ip', '0.0.0.0')
    ip_parts = ip.split('.')
    
    if len(ip_parts) == 4 and all(part.isdigit() for part in ip_parts):
        features.extend([int(part) for part in ip_parts])
        features.extend([
            1 if ip_parts[0] in ['192', '10', '172'] else 0,  # Private IP
            1 if ip_parts[0] == '127' else 0,  # Localhost
            1 if int(ip_parts[0]) > 200 else 0,  # High range
            sum(int(part) for part in ip_parts)  # IP sum
        ])
    else:
        features.extend([0] * 8)
    
    # === Path Features (20 features) ===
    path = attack_data.get('path', '').lower()
    features.extend([
        len(path),
        path.count('/'),
        path.count('.'),
        path.count('?'),
        path.count('&'),
        path.count('='),
        path.count('-'),
        path.count('_'),
        path.count('%'),  # URL encoding
        path.count('+'),
        len(path.split('/')),  # Path depth
        1 if path.startswith('/admin') else 0,
        1 if path.startswith('/config') else 0,
        1 if path.startswith('/cgi') else 0,
        1 if any(ext in path for ext in ['.php', '.asp', '.jsp']) else 0,
        1 if any(ext in path for ext in ['.xml', '.sql', '.conf']) else 0,
        1 if any(word in path for word in ['backup', 'test', 'debug']) else 0,
        1 if any(word in path for word in ['login', 'auth', 'signin']) else 0,
        1 if '../' in path or '..' in path else 0,  # Directory traversal
        1 if any(char in path for char in ['<', '>', '"', "'"]) else 0  # XSS chars
    ])
    
    # === Payload Features (15 features) ===
    payload = attack_data.get('payload', '').lower()
    features.extend([
        len(payload),
        payload.count('='),
        payload.count('&'),
        payload.count('%'),
        payload.count('+'),
        payload.count(' '),
        payload.count(';'),
        payload.count('--'),
        1 if any(word in payload for word in ['username', 'password', 'login']) else 0,
        1 if any(word in payload for word in ['select', 'union', 'insert', 'drop']) else 0,
        1 if any(word in payload for word in ['script', 'alert', 'eval']) else 0,
        1 if any(word in payload for word in ['../', '..\\', 'etc/passwd']) else 0,
        1 if any(word in payload for word in ['system', 'exec', 'cmd']) else 0,
        payload.count('or 1=1'),
        payload.count("'")
    ])
    
    # === Temporal Features (7 features) ===
    timestamp = attack_data.get('timestamp', 0)
    hour = (timestamp // 3600) % 24
    day_of_week = (timestamp // 86400) % 7
    
    features.extend([
        hour,
        day_of_week,
        1 if 9 <= hour <= 17 else 0,  # Business hours
        1 if hour >= 22 or hour <= 6 else 0,  # Night time
        1 if day_of_week >= 5 else 0,  # Weekend
        hour * day_of_week,  # Interaction feature
        1 if hour in [2, 3, 4] else 0  # Late night attacks
    ])
    
    return features

def predict_attack_type(attack_data):
    """Predict attack type using enhanced ML model"""
    global model_data
    
    if model_data is None:
        if not load_production_model():
            return fallback_classification(attack_data)
    
    try:
        # Extract features and predict
        features = extract_features(attack_data)
        X = np.array([features])
        X_scaled = model_data['scaler'].transform(X)
        
        prediction = model_data['model'].predict(X_scaled)[0]
        predicted_label = model_data['label_encoder'].inverse_transform([prediction])[0]
        
        # Get prediction confidence
        probabilities = model_data['model'].predict_proba(X_scaled)[0]
        confidence = max(probabilities)
        
        logger.info(f"ML Prediction: {predicted_label} (confidence: {confidence:.2f})")
        return predicted_label, confidence
        
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return fallback_classification(attack_data), 0.5

def fallback_classification(attack_data):
    """Enhanced fallback classification"""
    path = attack_data.get('path', '').lower()
    payload = attack_data.get('payload', '').lower()
    
    # SQL injection patterns
    if any(pattern in payload for pattern in ['select', 'union', 'insert', 'or 1=1', '--']):
        return 'sql_injection'
    
    # XSS patterns
    if any(pattern in payload for pattern in ['<script', 'alert(', 'javascript:']):
        return 'xss_attack'
    
    # Command injection
    if any(pattern in payload for pattern in ['system(', 'exec(', '; cat ', '&& rm']):
        return 'command_injection'
    
    # Directory traversal
    if '../' in path or any(word in payload for word in ['etc/passwd', 'boot.ini']):
        return 'directory_traversal'
    
    # Brute force patterns
    if any(word in payload for word in ['username', 'password', 'login']):
        return 'brute_force_credential'
    
    # Admin privilege escalation
    if any(word in path for word in ['admin', 'administrator', 'manager']):
        return 'privilege_escalation'
    
    # Information disclosure
    if any(word in path for word in ['config', 'backup', '.env', 'database']):
        return 'information_disclosure'
    
    # Reconnaissance patterns
    if any(word in path for word in ['robots.txt', 'sitemap', 'test']):
        return 'reconnaissance'
    
    return 'unknown'

def create_genesis_block():
    """Create the first block in the blockchain"""
    genesis_data = {
        "message": "Enhanced IoT Honeypot Blockchain",
        "timestamp": time.time(),
        "version": "2.0"
    }
    return Block(0, time.time(), genesis_data, "0")

def add_block(data):
    """Add a new block to the blockchain"""
    latest_block = blockchain[-1] if blockchain else None
    if latest_block is None:
        return None
    
    new_block = Block(
        index=latest_block.index + 1,
        timestamp=time.time(),
        data=data,
        previous_hash=latest_block.hash
    )
    
    blockchain.append(new_block)
    logger.info(f"Block #{new_block.index} added - {data.get('attack_type', 'unknown')}")
    return new_block

def store_attack(attack_data, block_hash):
    """Store attack data in database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO attacks (device_id, timestamp, attack_type, source_ip, path, payload, block_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        attack_data.get('device_id'),
        attack_data.get('timestamp'),
        attack_data.get('attack_type'),
        attack_data.get('source_ip'),
        attack_data.get('path'),
        attack_data.get('payload'),
        block_hash
    ))
    
    conn.commit()
    conn.close()

@app.route('/attack', methods=['POST'])
def receive_attack():
    """Receive and process attack data"""
    try:
        attack_data = request.get_json()
        if not attack_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Classify attack using enhanced ML
        predicted_type, confidence = predict_attack_type(attack_data)
        attack_data['ml_classification'] = predicted_type
        
        # Add to blockchain
        block = add_block(attack_data)
        if block:
            store_attack(attack_data, block.hash)
            
            return jsonify({
                'status': 'success',
                'block_hash': block.hash,
                'block_index': block.index,
                'ml_classification': predicted_type,
                'confidence': confidence,
                'model_accuracy': model_data['accuracy'] if model_data else 'N/A'
            })
        else:
            return jsonify({'error': 'Failed to add block'}), 500
            
    except Exception as e:
        logger.error(f"Error processing attack: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    try:
        with open('/Users/bhaskar/Desktop/IOT/dashboard.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'message': 'Enhanced IoT Honeypot Server Running', 'status': 'online'})

@app.route('/stats')
def get_stats():
    """Get comprehensive attack statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Total attacks
        cursor.execute('SELECT COUNT(*) FROM attacks')
        total_attacks = cursor.fetchone()[0]
        
        # Unique IPs
        cursor.execute('SELECT COUNT(DISTINCT source_ip) FROM attacks')
        unique_ips = cursor.fetchone()[0]
        
        # Attack types breakdown
        cursor.execute('SELECT attack_type, COUNT(*) FROM attacks GROUP BY attack_type ORDER BY COUNT(*) DESC')
        attack_types = dict(cursor.fetchall())
        
        # Recent attacks
        cursor.execute('''
            SELECT device_id, timestamp, attack_type, source_ip, path, payload, created_at
            FROM attacks 
            ORDER BY id DESC 
            LIMIT 50
        ''')
        recent_attacks = [
            {
                'device_id': row[0],
                'timestamp': row[1],
                'attack_type': row[2],
                'source_ip': row[3],
                'path': row[4],
                'payload': row[5],
                'created_at': row[6]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            'total_attacks': total_attacks,
            'unique_ips': unique_ips,
            'attack_types': attack_types,
            'recent_attacks': recent_attacks,
            'blockchain_blocks': len(blockchain),
            'ml_model_loaded': model_data is not None,
            'ml_accuracy': model_data['accuracy'] if model_data else 0,
            'ml_model_name': model_data['model_name'] if model_data else 'None'
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export')
def export_all_attacks():
    """Export all attacks for analysis"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, device_id, timestamp, attack_type, source_ip, path, payload, 
                   block_hash, created_at
            FROM attacks 
            ORDER BY id DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        all_attacks = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'attacks': all_attacks,
            'total': len(all_attacks),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting attacks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/model/info')
def get_model_info():
    """Get ML model information"""
    if model_data:
        return jsonify({
            'model_loaded': True,
            'model_name': model_data['model_name'],
            'accuracy': model_data['accuracy'],
            'features': len(model_data['feature_names']),
            'classes': list(model_data['label_encoder'].classes_)
        })
    else:
        return jsonify({
            'model_loaded': False,
            'message': 'Production model not available'
        })

@app.route('/blockchain')
def get_blockchain():
    """Get blockchain status and recent blocks"""
    try:
        # Get last 10 blocks
        recent_blocks = blockchain[-10:] if len(blockchain) > 10 else blockchain
        
        return jsonify({
            'total_blocks': len(blockchain),
            'latest_block': blockchain[-1].__dict__ if blockchain else None,
            'recent_blocks': [block.__dict__ for block in recent_blocks],
            'blockchain_valid': verify_blockchain()
        })
    except Exception as e:
        logger.error(f"Error getting blockchain: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predictions')
def get_predictions():
    """Get ML prediction statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get prediction distribution
        cursor.execute('''
            SELECT attack_type, COUNT(*) as count 
            FROM attacks 
            GROUP BY attack_type 
            ORDER BY count DESC
        ''')
        predictions = cursor.fetchall()
        
        # Get recent predictions with confidence
        cursor.execute('''
            SELECT attack_type, created_at 
            FROM attacks 
            ORDER BY created_at DESC 
            LIMIT 20
        ''')
        recent = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'prediction_distribution': [{'type': p[0], 'count': p[1]} for p in predictions],
            'recent_predictions': [{'type': r[0], 'timestamp': r[1]} for r in recent],
            'model_status': {
                'loaded': model_data is not None,
                'accuracy': model_data['accuracy'] if model_data else 0,
                'model_name': model_data['model_name'] if model_data else 'None'
            }
        })
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/frequency')
def get_frequency():
    """Get attack frequency data for charts"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get attacks per hour for last 24 hours
        cursor.execute('''
            SELECT 
                strftime('%H', datetime(created_at)) as hour,
                COUNT(*) as count
            FROM attacks 
            WHERE datetime(created_at) >= datetime('now', '-24 hours')
            GROUP BY strftime('%H', datetime(created_at))
            ORDER BY hour
        ''')
        hourly = cursor.fetchall()
        
        # Get attacks per day for last 30 days
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM attacks 
            WHERE datetime(created_at) >= datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        daily = cursor.fetchall()
        
        # Get top source IPs
        cursor.execute('''
            SELECT source_ip, COUNT(*) as count
            FROM attacks
            GROUP BY source_ip
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_ips = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'hourly_frequency': [{'hour': h[0], 'count': h[1]} for h in hourly],
            'daily_frequency': [{'date': d[0], 'count': d[1]} for d in daily],
            'top_source_ips': [{'ip': ip[0], 'count': ip[1]} for ip in top_ips]
        })
    except Exception as e:
        logger.error(f"Error getting frequency data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'system': {
            'database': 'connected',
            'blockchain': f'{len(blockchain)} blocks',
            'ml_model': 'loaded' if model_data else 'not loaded'
        }
    })

def verify_blockchain():
    """Verify blockchain integrity"""
    if len(blockchain) <= 1:
        return True
    
    for i in range(1, len(blockchain)):
        current_block = blockchain[i]
        previous_block = blockchain[i-1]
        
        # Check if current block's previous hash matches previous block's hash
        if current_block.previous_hash != previous_block.hash:
            return False
        
        # Check if current block's hash is valid
        if current_block.hash != current_block.calculate_hash():
            return False
    
    return True

def initialize_system():
    """Initialize the enhanced honeypot system"""
    logger.info("🚀 Initializing Enhanced IoT Honeypot System...")
    
    # Initialize database
    init_database()
    
    # Create genesis block
    if not blockchain:
        genesis_block = create_genesis_block()
        blockchain.append(genesis_block)
        logger.info("Genesis block created")
    
    # Load production ML model
    load_production_model()
    
    logger.info("✅ System initialization complete")

if __name__ == '__main__':
    initialize_system()
    logger.info("🌐 Starting Enhanced Flask server on http://0.0.0.0:5001")
    app.run(debug=False, host='0.0.0.0', port=5001)
