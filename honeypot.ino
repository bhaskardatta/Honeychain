// IoT Honeypot - ESP32 Arduino Code
// Emulates vulnerable IP camera to attract and log attacks
// Sends attack data to local Flask server for blockchain storage and AI analysis

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>

// WiFi Configuration - CHANGE THESE FOR YOUR NETWORK
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server Configuration - CHANGE THIS TO YOUR COMPUTER'S IP
const char* serverURL = "http://YOUR_SERVER_IP:5001/attack";

// Device Configuration
const String device_id = "ESP32_HONEYPOT_001";
const String device_model = "SecureCam Pro 2000";
const String firmware_version = "v1.2.3";

WebServer server(80);
unsigned long attackCount = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== IoT Honeypot Starting ===");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Setup web server routes
  setupRoutes();
  
  server.begin();
  Serial.println("Honeypot web server started on port 80");
  Serial.println("Waiting for attacks...");
}

void setupRoutes() {
  // Main camera login page
  server.on("/", HTTP_GET, handleRoot);
  server.on("/", HTTP_POST, handleLogin);
  
  // Common vulnerable endpoints
  server.on("/admin", handleAdmin);
  server.on("/config.xml", handleConfig);
  server.on("/setup", handleSetup);
  server.on("/cgi-bin/", handleCGI);
  server.on("/cgi-bin/admin.cgi", handleCGI);
  server.on("/HNAP1/", handleHNAP);
  server.on("/goform/", handleGoForm);
  
  // Handle 404s as reconnaissance attempts
  server.onNotFound(handle404);
}

void loop() {
  server.handleClient();
  delay(10);
}

void handleRoot() {
  logAttack("web_access", server.client().remoteIP().toString(), "/", "");
  
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>SecureCam Pro 2000 - Login</title>
    <style>
        body { font-family: Arial; background: #f0f0f0; margin: 0; padding: 20px; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { text-align: center; color: #333; margin-bottom: 30px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #555; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .btn { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .info { margin-top: 20px; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h2>🔒 SecureCam Pro 2000</h2>
            <p>Network Camera System</p>
        </div>
        <form method="POST" action="/">
            <div class="form-group">
                <label>Username:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
        <div class="info">
            <strong>Device Info:</strong><br>
            Model: SecureCam Pro 2000<br>
            Firmware: v1.2.3<br>
            Status: Online
        </div>
    </div>
</body>
</html>
  )";
  
  server.send(200, "text/html", html);
}

void handleLogin() {
  String username = server.arg("username");
  String password = server.arg("password");
  String payload = "username=" + username + "&password=" + password;
  
  logAttack("brute_force", server.client().remoteIP().toString(), "/", payload);
  
  // Always reject login attempts
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>Login Failed - SecureCam Pro 2000</title>
    <style>
        body { font-family: Arial; background: #f0f0f0; margin: 0; padding: 20px; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .error { color: #dc3545; margin-bottom: 20px; }
        .btn { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="error">
            <h3>❌ Login Failed</h3>
            <p>Invalid username or password</p>
        </div>
        <a href="/" class="btn">Try Again</a>
    </div>
</body>
</html>
  )";
  
  server.send(401, "text/html", html);
}

void handleAdmin() {
  logAttack("admin_access", server.client().remoteIP().toString(), "/admin", "");
  
  String html = R"(
<!DOCTYPE html>
<html>
<head><title>Admin Panel - Access Denied</title></head>
<body style="font-family: Arial; text-align: center; margin-top: 100px;">
    <h2>🚫 Access Denied</h2>
    <p>Administrator login required</p>
    <p>Contact system administrator</p>
</body>
</html>
  )";
  
  server.send(403, "text/html", html);
}

void handleConfig() {
  logAttack("config_access", server.client().remoteIP().toString(), "/config.xml", "");
  
  String xml = R"(<?xml version="1.0" encoding="UTF-8"?>
<config>
    <device>
        <model>SecureCam Pro 2000</model>
        <version>1.2.3</version>
        <serial>SC2000-78945612</serial>
    </device>
    <network>
        <dhcp>enabled</dhcp>
        <port>80</port>
    </network>
    <security>
        <auth>required</auth>
        <encryption>WPA2</encryption>
    </security>
</config>)";
  
  server.send(200, "application/xml", xml);
}

void handleSetup() {
  logAttack("setup_access", server.client().remoteIP().toString(), "/setup", "");
  server.send(404, "text/plain", "Setup page not found");
}

void handleCGI() {
  String path = server.uri();
  logAttack("cgi_exploit", server.client().remoteIP().toString(), path, "");
  server.send(500, "text/plain", "CGI Error");
}

void handleHNAP() {
  logAttack("hnap_exploit", server.client().remoteIP().toString(), "/HNAP1/", "");
  server.send(404, "text/plain", "HNAP service not available");
}

void handleGoForm() {
  logAttack("goform_exploit", server.client().remoteIP().toString(), "/goform/", "");
  server.send(404, "text/plain", "GoForm service not available");
}

void handle404() {
  String path = server.uri();
  logAttack("reconnaissance", server.client().remoteIP().toString(), path, "");
  
  String html = R"(
<!DOCTYPE html>
<html>
<head><title>404 - Page Not Found</title></head>
<body style="font-family: Arial; text-align: center; margin-top: 100px;">
    <h2>404 - Page Not Found</h2>
    <p>The requested resource was not found on this server.</p>
    <hr>
    <small>SecureCam Pro 2000 Web Server</small>
</body>
</html>
  )";
  
  server.send(404, "text/html", html);
}

void logAttack(String attackType, String sourceIP, String path, String payload) {
  attackCount++;
  
  // Print to serial for debugging
  Serial.println("\n=== ATTACK DETECTED ===");
  Serial.println("Count: " + String(attackCount));
  Serial.println("Type: " + attackType);
  Serial.println("Source IP: " + sourceIP);
  Serial.println("Path: " + path);
  Serial.println("Payload: " + payload);
  Serial.println("Time: " + String(millis()));
  Serial.println("=======================");
  
  // Send to server
  sendToServer(attackType, sourceIP, path, payload);
}

void sendToServer(String attackType, String sourceIP, String path, String payload) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    DynamicJsonDocument doc(1024);
    doc["device_id"] = device_id;
    doc["timestamp"] = millis();
    doc["attack_type"] = attackType;
    doc["source_ip"] = sourceIP;
    doc["path"] = path;
    doc["payload"] = payload;
    doc["device_model"] = device_model;
    doc["firmware_version"] = firmware_version;
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
      Serial.println("Data sent to server successfully");
    } else {
      Serial.println("Error sending data to server: " + String(httpResponseCode));
    }
    
    http.end();
  } else {
    Serial.println("WiFi not connected - cannot send data");
  }
}
