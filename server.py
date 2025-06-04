#!/usr/bin/env python3
"""
IoT Honeypot Server with Blockchain and AI Analysis
Complete Flask server that receives attack data from ESP32 honeypots,
stores in blockchain, analyzes with ML, and provides web dashboard
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import hashlib
import json
import time
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import pickle
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables
blockchain = []
ml_model = None
vectorizer = None
label_encoder = None
model_trained = False
attack_counter = 0
RETRAIN_THRESHOLD = 50

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
    conn = sqlite3.connect('honeypot.db')
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

def create_genesis_block():
    """Create the first block in the blockchain"""
    genesis_data = {
        "message": "Genesis Block - IoT Honeypot Blockchain",
        "timestamp": time.time(),
        "attacks": 0
    }
    return Block(0, time.time(), genesis_data, "0")

def get_latest_block():
    """Get the most recent block in the blockchain"""
    return blockchain[-1] if blockchain else None

def add_block(data):
    """Add a new block to the blockchain"""
    latest_block = get_latest_block()
    if latest_block is None:
        # This shouldn't happen if genesis block is created
        return None
    
    new_block = Block(
        index=latest_block.index + 1,
        timestamp=time.time(),
        data=data,
        previous_hash=latest_block.hash
    )
    
    blockchain.append(new_block)
    logger.info(f"New block added: #{new_block.index} - Hash: {new_block.hash[:16]}...")
    return new_block

def store_attack(attack_data, block_hash):
    """Store attack data in SQLite database"""
    conn = sqlite3.connect('honeypot.db')
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

def extract_features(attack_data):
    """Extract features from attack data for ML classification"""
    features = []
    
    # IP-based features
    ip_parts = attack_data.get('source_ip', '0.0.0.0').split('.')
    ip_numeric = sum(int(part) * (256 ** (3-i)) for i, part in enumerate(ip_parts) if part.isdigit())
    features.append(ip_numeric % 10000)  # Normalize IP
    
    # Path-based features
    path = attack_data.get('path', '')
    features.extend([
        len(path),
        path.count('/'),
        path.count('.'),
        path.count('?'),
        1 if 'admin' in path.lower() else 0,
        1 if 'config' in path.lower() else 0,
        1 if 'cgi' in path.lower() else 0,
    ])
    
    # Payload-based features
    payload = attack_data.get('payload', '')
    features.extend([
        len(payload),
        payload.count('='),
        payload.count('&'),
        1 if 'password' in payload.lower() else 0,
        1 if 'username' in payload.lower() else 0,
    ])
    
    # Time-based features
    timestamp = attack_data.get('timestamp', 0)
    hour = (timestamp // 3600) % 24
    features.append(hour)
    
    return features

def classify_attack_simple(attack_data):
    """Simple rule-based classification for initial training data"""
    attack_type = attack_data.get('attack_type', 'unknown')
    path = attack_data.get('path', '').lower()
    payload = attack_data.get('payload', '').lower()
    
    if 'password' in payload and 'username' in payload:
        return 'brute_force'
    elif 'admin' in path or 'config' in path:
        return 'privilege_escalation'
    elif 'cgi' in path or 'exploit' in path:
        return 'exploitation'
    elif len(path) > 1 and attack_type == 'reconnaissance':
        return 'reconnaissance'
    else:
        return 'unknown'

def train_ml_model():
    """Train machine learning model on accumulated attack data"""
    global ml_model, vectorizer, label_encoder, model_trained
    
    conn = sqlite3.connect('honeypot.db')
    df = pd.read_sql_query('SELECT * FROM attacks', conn)
    conn.close()
    
    if len(df) < 10:
        logger.info("Not enough data to train ML model")
        return False
    
    # Extract features
    features = []
    labels = []
    
    for _, row in df.iterrows():
        attack_data = {
            'source_ip': row['source_ip'],
            'path': row['path'],
            'payload': row['payload'],
            'timestamp': row['timestamp'],
            'attack_type': row['attack_type']
        }
        
        feature_vector = extract_features(attack_data)
        features.append(feature_vector)
        
        # Use simple classification for training labels
        true_label = classify_attack_simple(attack_data)
        labels.append(true_label)
    
    # Train model
    X = np.array(features)
    y = np.array(labels)
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Train Random Forest
    ml_model = RandomForestClassifier(n_estimators=50, random_state=42)
    ml_model.fit(X, y_encoded)
    
    model_trained = True
    logger.info(f"ML model trained on {len(X)} samples with {len(set(y))} classes")
    return True

def predict_attack_type(attack_data):
    """Predict attack type using trained ML model"""
    if not model_trained or ml_model is None:
        return classify_attack_simple(attack_data)
    
    try:
        features = extract_features(attack_data)
        X = np.array([features])
        
        prediction = ml_model.predict(X)[0]
        predicted_label = label_encoder.inverse_transform([prediction])[0]
        
        # Get prediction confidence
        probabilities = ml_model.predict_proba(X)[0]
        confidence = max(probabilities)
        
        logger.info(f"ML Prediction: {predicted_label} (confidence: {confidence:.2f})")
        return predicted_label
        
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return classify_attack_simple(attack_data)

@app.route('/attack', methods=['POST'])
def receive_attack():
    """Receive attack data from ESP32 honeypot"""
    global attack_counter
    
    try:
        attack_data = request.get_json()
        if not attack_data:
            return jsonify({'error': 'No data received'}), 400
        
        logger.info(f"Attack received from {attack_data.get('source_ip', 'unknown')} - Type: {attack_data.get('attack_type', 'unknown')}")
        
        # Classify attack using ML
        predicted_type = predict_attack_type(attack_data)
        attack_data['ml_classification'] = predicted_type
        
        # Add to blockchain
        block = add_block(attack_data)
        if block:
            # Store in database
            store_attack(attack_data, block.hash)
            attack_counter += 1
            
            # Retrain model periodically
            if attack_counter % RETRAIN_THRESHOLD == 0:
                logger.info("Retraining ML model...")
                train_ml_model()
            
            return jsonify({
                'status': 'success',
                'block_hash': block.hash,
                'block_index': block.index,
                'ml_classification': predicted_type
            })
        else:
            return jsonify({'error': 'Failed to add block'}), 500
            
    except Exception as e:
        logger.error(f"Error processing attack: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    with open('/Users/bhaskar/Desktop/IOT/dashboard.html', 'r') as f:
        return f.read()

@app.route('/stats')
def get_stats():
    """Get attack statistics"""
    try:
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        # Total attacks
        cursor.execute('SELECT COUNT(*) FROM attacks')
        total_attacks = cursor.fetchone()[0]
        
        # Unique IPs
        cursor.execute('SELECT COUNT(DISTINCT source_ip) FROM attacks')
        unique_ips = cursor.fetchone()[0]
        
        # Attack types breakdown
        cursor.execute('SELECT attack_type, COUNT(*) FROM attacks GROUP BY attack_type')
        attack_types = dict(cursor.fetchall())
        
        # Recent attacks
        cursor.execute('''
            SELECT device_id, timestamp, attack_type, source_ip, path, payload, created_at
            FROM attacks 
            ORDER BY id DESC 
            LIMIT 20
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
            'ml_model_trained': model_trained
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/blockchain')
def get_blockchain():
    """Get full blockchain data"""
    try:
        blockchain_data = [block.to_dict() for block in blockchain]
        return jsonify({
            'blocks': blockchain_data,
            'total_blocks': len(blockchain),
            'latest_hash': blockchain[-1].hash if blockchain else None
        })
    except Exception as e:
        logger.error(f"Error getting blockchain: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predictions')
def get_predictions():
    """Get ML model predictions and accuracy"""
    try:
        if not model_trained:
            return jsonify({
                'model_trained': False,
                'message': 'Model not yet trained'
            })
        
        conn = sqlite3.connect('honeypot.db')
        df = pd.read_sql_query('SELECT * FROM attacks ORDER BY id DESC LIMIT 100', conn)
        conn.close()
        
        predictions = []
        for _, row in df.iterrows():
            attack_data = {
                'source_ip': row['source_ip'],
                'path': row['path'],
                'payload': row['payload'],
                'timestamp': row['timestamp'],
                'attack_type': row['attack_type']
            }
            
            ml_prediction = predict_attack_type(attack_data)
            simple_prediction = classify_attack_simple(attack_data)
            
            predictions.append({
                'id': row['id'],
                'source_ip': row['source_ip'],
                'original_type': row['attack_type'],
                'ml_prediction': ml_prediction,
                'rule_based': simple_prediction,
                'timestamp': row['timestamp']
            })
        
        return jsonify({
            'model_trained': True,
            'predictions': predictions[:20],  # Last 20 predictions
            'total_predictions': len(predictions)
        })
        
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/frequency')
def get_attack_frequency():
    """Get attack frequency data for charts"""
    try:
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        # Get attacks from last 24 hours, grouped by hour
        twenty_four_hours_ago = time.time() - (24 * 3600)
        
        cursor.execute('''
            SELECT 
                strftime('%H', datetime(created_at)) as hour,
                COUNT(*) as count,
                attack_type
            FROM attacks 
            WHERE created_at >= ?
            GROUP BY hour, attack_type
            ORDER BY hour
        ''', (datetime.fromtimestamp(twenty_four_hours_ago).strftime('%Y-%m-%d %H:%M:%S'),))
        
        results = cursor.fetchall()
        conn.close()
        
        # Create 24-hour data structure
        hourly_data = {}
        attack_type_hourly = {}
        
        # Initialize all hours with 0
        for i in range(24):
            hour_str = f"{i:02d}"
            hourly_data[hour_str] = 0
            attack_type_hourly[hour_str] = {}
        
        # Fill in actual data
        for hour, count, attack_type in results:
            if hour:
                hourly_data[hour] = hourly_data.get(hour, 0) + count
                if hour not in attack_type_hourly:
                    attack_type_hourly[hour] = {}
                attack_type_hourly[hour][attack_type] = count
        
        # Prepare chart data
        current_hour = int(datetime.now().strftime('%H'))
        labels = []
        data = []
        
        # Create labels starting from current hour going back 24 hours
        for i in range(24):
            hour = (current_hour - 23 + i) % 24
            hour_str = f"{hour:02d}:00"
            labels.append(hour_str)
            data.append(hourly_data.get(f"{hour:02d}", 0))
        
        return jsonify({
            'labels': labels,
            'data': data,
            'hourly_breakdown': attack_type_hourly,
            'total_attacks_24h': sum(data)
        })
        
    except Exception as e:
        logger.error(f"Error getting frequency data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export')
def export_all_attacks():
    """Export all attacks for CSV download"""
    try:
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        # Get ALL attacks, not just recent ones
        cursor.execute('''
            SELECT 
                id, device_id, timestamp, attack_type, source_ip, path, payload, 
                block_hash, created_at
            FROM attacks 
            ORDER BY id DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        all_attacks = []
        
        for row in cursor.fetchall():
            attack = dict(zip(columns, row))
            all_attacks.append(attack)
        
        conn.close()
        
        logger.info(f"Exporting {len(all_attacks)} attacks as CSV data")
        return jsonify({
            'attacks': all_attacks,
            'total': len(all_attacks),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting attacks: {e}")
        return jsonify({'error': str(e)}), 500

def initialize_system():
    """Initialize the entire honeypot system"""
    logger.info("Initializing IoT Honeypot System...")
    
    # Initialize database
    init_database()
    
    # Create genesis block
    if not blockchain:
        genesis_block = create_genesis_block()
        blockchain.append(genesis_block)
        logger.info("Genesis block created")
    
    # Try to train initial model
    train_ml_model()
    
    logger.info("System initialization complete")

if __name__ == '__main__':
    initialize_system()
    logger.info("Starting Flask server on http://0.0.0.0:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
