#!/bin/bash

# HoneyChain IoT Honeypot - Quick Setup Script
# This script sets up the Python environment and starts the server

echo "🛡️  HoneyChain IoT Honeypot Setup"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Get local IP address
LOCAL_IP=$(ifconfig | grep -E "inet.*broadcast" | awk '{print $2}' | head -1)

echo ""
echo "🚀 Setup Complete!"
echo "=================="
echo "1. Update ESP32 code with your WiFi credentials"
echo "2. Set server URL in ESP32 to: http://$LOCAL_IP:5000/attack"
echo "3. Upload ESP32 code using Arduino IDE"
echo "4. Run this script again with 'start' parameter to launch server"
echo ""
echo "Your computer's IP address: $LOCAL_IP"
echo ""

# If 'start' parameter is provided, start the server
if [ "$1" = "start" ]; then
    echo "🌐 Starting HoneyChain server..."
    echo "Dashboard will be available at: http://localhost:5000"
    echo "Press Ctrl+C to stop the server"
    echo ""
    python3 server.py
fi
