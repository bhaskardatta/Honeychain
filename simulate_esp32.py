#!/usr/bin/env python3
"""
ESP32 Honeypot Simulator
Simulates attacks being sent from ESP32 to test the complete system
"""

import requests
import json
import time
import random

SERVER_URL = "http://localhost:5001/attack"

# Sample attack scenarios
ATTACK_SCENARIOS = [
    {
        "attack_type": "brute_force",
        "path": "/",
        "payloads": [
            "username=admin&password=admin",
            "username=admin&password=123456",
            "username=root&password=root",
            "username=admin&password=password",
            "username=user&password=user"
        ]
    },
    {
        "attack_type": "admin_access",
        "path": "/admin",
        "payloads": [""]
    },
    {
        "attack_type": "config_access", 
        "path": "/config.xml",
        "payloads": [""]
    },
    {
        "attack_type": "reconnaissance",
        "path": "/robots.txt",
        "payloads": [""]
    },
    {
        "attack_type": "reconnaissance",
        "path": "/backup.sql",
        "payloads": [""]
    },
    {
        "attack_type": "cgi_exploit",
        "path": "/cgi-bin/admin.cgi",
        "payloads": [""]
    },
    {
        "attack_type": "setup_access",
        "path": "/setup",
        "payloads": [""]
    }
]

# Sample IP addresses to simulate different attackers
ATTACKER_IPS = [
    "192.168.1.100", "10.0.0.50", "172.16.0.88", "203.0.113.25",
    "198.51.100.42", "192.168.1.200", "10.0.0.75", "172.16.0.99",
    "192.168.0.150", "10.0.0.33", "198.51.100.88", "203.0.113.50"
]

def send_attack(attack_type, source_ip, path, payload):
    """Send attack data to the server"""
    attack_data = {
        "device_id": "ESP32_HONEYPOT_001",
        "timestamp": int(time.time() * 1000),
        "attack_type": attack_type,
        "source_ip": source_ip,
        "path": path,
        "payload": payload,
        "device_model": "SecureCam Pro 2000",
        "firmware_version": "v1.2.3"
    }
    
    try:
        response = requests.post(SERVER_URL, json=attack_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Attack logged: {attack_type} from {source_ip} → Block #{result['block_index']}")
            print(f"   ML Classification: {result['ml_classification']}")
            return True
        else:
            print(f"❌ Failed to send attack: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending attack: {e}")
        return False

def simulate_attack_wave():
    """Simulate a wave of attacks"""
    print("🚨 Simulating ESP32 honeypot under attack...")
    print("=" * 50)
    
    for i in range(10):
        # Choose random attack scenario
        scenario = random.choice(ATTACK_SCENARIOS)
        attack_type = scenario["attack_type"]
        path = scenario["path"]
        payload = random.choice(scenario["payloads"])
        source_ip = random.choice(ATTACKER_IPS)
        
        # Send attack
        send_attack(attack_type, source_ip, path, payload)
        
        # Wait between attacks (1-3 seconds)
        time.sleep(random.uniform(1, 3))
    
    print("=" * 50)
    print("🎯 Attack simulation complete!")
    print("Check the dashboard at http://localhost:5001 to see results")

if __name__ == "__main__":
    print("🛡️ ESP32 Honeypot Attack Simulator")
    print("This simulates attacks being detected by the ESP32 honeypot")
    print()
    
    try:
        simulate_attack_wave()
    except KeyboardInterrupt:
        print("\n⏹️ Simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
