# 🛡️ ESP32 Honeypot Simulator - Usage Guide

## Overview
The ESP32 simulator (`simulate_esp32.py`) is a powerful tool for testing the complete IoT honeypot system without requiring physical ESP32 hardware. It simulates realistic attacks and sends them to the server for ML analysis and blockchain storage.

## Key Features

### 🎯 **15 Attack Types Supported**
- `brute_force_credential` - Login brute force attacks
- `sql_injection` - SQL injection attempts  
- `xss_attack` - Cross-site scripting attacks
- `directory_traversal` - Path traversal attacks
- `command_injection` - Command injection attempts
- `privilege_escalation` - Privilege escalation attacks
- `information_disclosure` - Information disclosure attempts
- `reconnaissance` - Reconnaissance and scanning
- `file_upload_attack` - Malicious file uploads
- `ddos_simulation` - Distributed denial of service

### 🤖 **5 Virtual ESP32 Devices**
- `ESP32_HONEYPOT_001` - SecureCam Pro 2000 (Front Door)
- `ESP32_HONEYPOT_002` - IoTDevice X1 (Back Yard)
- `ESP32_HONEYPOT_003` - SmartSensor v3 (Garage)
- `ESP32_HONEYPOT_004` - WiFiCam Elite (Living Room)
- `ESP32_HONEYPOT_005` - SecureWatch Pro (Office)

### 🌐 **Realistic IP Pools**
- Residential networks (192.168.x.x)
- Corporate networks (172.16.x.x)
- Public suspicious IPs (203.0.113.x)
- Tor exit nodes (198.51.100.x)
- Cloud providers (10.x.x.x)

## Usage Modes

### 1. **Interactive Mode** (Default)
```bash
python simulate_esp32.py
```
Provides a menu-driven interface with options for different simulation types.

### 2. **Attack Wave Mode**
```bash
# Simulate 10 random attacks with 1-3 second delays
python simulate_esp32.py --mode wave --attacks 10

# Custom wave with specific timing
python simulate_esp32.py --mode wave --attacks 20 --delay 0.5 2.0
```

### 3. **Targeted Campaign Mode**
```bash
# SQL injection and XSS campaign for 5 minutes
python simulate_esp32.py --mode campaign --attack-types sql_injection xss_attack --duration 300

# Brute force campaign
python simulate_esp32.py --mode campaign --attack-types brute_force_credential --duration 120
```

### 4. **DDoS Simulation Mode**
```bash
# Medium intensity DDoS for 30 seconds
python simulate_esp32.py --mode ddos --intensity medium --duration 30

# High intensity DDoS for 60 seconds  
python simulate_esp32.py --mode ddos --intensity high --duration 60
```

## Example Scenarios

### 🔒 **Security Testing**
```bash
# Test all attack types in sequence
python simulate_esp32.py --mode wave --attacks 50

# Focus on injection attacks
python simulate_esp32.py --mode campaign --attack-types sql_injection command_injection xss_attack
```

### 📊 **ML Model Testing**
```bash
# Generate diverse dataset for ML training
python simulate_esp32.py --mode wave --attacks 100 --delay 0.1 1.0

# Test specific attack classification
python simulate_esp32.py --mode campaign --attack-types reconnaissance information_disclosure
```

### 💥 **Load Testing**
```bash
# Light load test
python simulate_esp32.py --mode ddos --intensity low --duration 60

# Stress test
python simulate_esp32.py --mode ddos --intensity extreme --duration 30
```

## Command Line Options

```
--server URL          Target server URL (default: http://localhost:5001/attack)
--attacks NUMBER      Number of attacks for wave mode (default: 10)
--delay MIN MAX       Delay range between attacks in seconds (default: 1 3)
--mode MODE           Simulation mode: wave, campaign, ddos, interactive
--attack-types LIST   Specific attack types for campaign mode
--intensity LEVEL     DDoS intensity: low, medium, high, extreme
--duration SECONDS    Duration for timed simulations (default: 30)
```

## Integration with System

### ✅ **Prerequisites**
1. Enhanced server must be running: `python server_enhanced.py`
2. Server should be accessible on port 5001
3. Python packages: `requests` (included in requirements.txt)

### 📊 **Monitoring Results**
- **Real-time Dashboard**: http://localhost:5001
- **Console Output**: Attack logs with ML classifications
- **Database**: All attacks stored in `honeypot.db`
- **Blockchain**: Immutable attack records

### 🧠 **ML Integration**
- Each simulated attack is processed by the ML model
- Real-time classification with confidence scores
- Results displayed in console and dashboard
- Perfect for testing model accuracy and performance

## Best Practices

### 🎯 **For Development**
- Start with interactive mode to understand features
- Use wave mode for general testing
- Test specific attack types with campaign mode

### 🔬 **For Research** 
- Generate large datasets with wave mode
- Use targeted campaigns to study specific attack patterns
- Combine with real ESP32 devices for hybrid testing

### 🛡️ **For Security Testing**
- Test system under various attack intensities
- Verify ML model accuracy across all attack types
- Validate blockchain integrity under load

## Troubleshooting

### ❌ **Common Issues**
- **Connection Failed**: Ensure server is running on port 5001
- **Low Success Rate**: Check server logs for errors
- **Slow Performance**: Reduce attack frequency or intensity

### 🔧 **Server Not Responding**
```bash
# Check if server is running
curl http://localhost:5001/health

# Start server if needed
python server_enhanced.py
```

### 📊 **View Results**
```bash
# Check database
sqlite3 honeypot.db "SELECT COUNT(*) FROM attacks;"

# View recent attacks  
sqlite3 honeypot.db "SELECT * FROM attacks ORDER BY created_at DESC LIMIT 10;"
```

## Advanced Usage

### 🔄 **Continuous Testing**
```bash
# Run continuous simulation in background
nohup python simulate_esp32.py --mode wave --attacks 1000 --delay 5 10 &
```

### 📈 **Performance Monitoring**
```bash
# High-frequency testing
python simulate_esp32.py --mode ddos --intensity extreme --duration 120

# Monitor system resources while testing
top -p $(pgrep -f server_enhanced.py)
```

### 🎭 **Custom Attack Scenarios**
Edit the `attack_scenarios` dictionary in the simulator to add custom attack patterns, payloads, and targeting logic.

---

**Ready to test your IoT honeypot system? Start with interactive mode and explore the various simulation options!**
