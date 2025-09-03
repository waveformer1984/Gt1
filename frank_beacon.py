#!/usr/bin/env python3
"""
🚨 FRANK HARDWARE VERIFICATION BEACON 🚨
Standalone visual notification for hardware upgrades
"""

import asyncio
import json
import time
import psutil
import platform
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading
import webbrowser

class BeaconHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_beacon_html().encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            status = self.get_hardware_status()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_hardware_status(self):
        """Get current hardware status"""
        try:
            # Memory check
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            # CPU check
            cpu_usage = psutil.cpu_percent(interval=0.1)
            cpu_cores = psutil.cpu_count()
            
            # Get CPU model
            cpu_model = "Unknown"
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            cpu_model = line.split(':')[1].strip()
                            break
            except:
                pass
            
            # Storage check
            storage_info = []
            try:
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        storage_info.append({
                            'device': partition.device,
                            'total_gb': round(usage.total / (1024**3), 1),
                            'used_percent': round((usage.used / usage.total) * 100, 1)
                        })
                    except:
                        continue
            except:
                pass
            
            # Environment check
            environment = "Physical System"
            try:
                result = subprocess.run(['systemd-detect-virt'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    virt_type = result.stdout.strip()
                    if virt_type == "docker":
                        environment = "Docker Container"
                    elif virt_type != "none":
                        environment = f"Virtualized ({virt_type})"
            except:
                pass
            
            return {
                'timestamp': datetime.now().isoformat(),
                'ram': {
                    'total_gb': round(memory_gb, 2),
                    'used_percent': memory.percent,
                    'available_gb': round(memory.available / (1024**3), 2),
                    'upgrade_detected': memory_gb >= 15,
                    'status': '✅ VERIFIED - 16GB Upgrade Successful' if memory_gb >= 15 else '❌ Standard Configuration'
                },
                'cpu': {
                    'model': cpu_model,
                    'cores': cpu_cores,
                    'usage_percent': cpu_usage,
                    'status': '✅ Professional Grade' if 'Xeon' in cpu_model else '✅ Good'
                },
                'storage': {
                    'devices': storage_info,
                    'external_ssd_detected': len([d for d in storage_info if d['total_gb'] > 800]) > 0,
                    'status': '⚠️ Check host system for 1TB external SSD'
                },
                'environment': {
                    'type': environment,
                    'hardware_access': 'Limited' if 'Container' in environment else 'Full'
                },
                'overall_health': {
                    'score': 90 if memory_gb >= 15 else 75,
                    'status': 'Excellent' if memory_gb >= 15 else 'Good'
                }
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'Error getting hardware status'
            }
    
    def get_beacon_html(self):
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 FRANK HARDWARE BEACON 🚨</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FECA57);
            background-size: 400% 400%;
            animation: gradientShift 8s ease infinite;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .beacon-container {
            text-align: center;
            background: rgba(0, 0, 0, 0.7);
            padding: 60px 40px;
            border-radius: 30px;
            backdrop-filter: blur(20px);
            border: 3px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
            max-width: 900px;
            width: 90vw;
            animation: containerPulse 3s ease-in-out infinite;
            position: relative;
            overflow: hidden;
        }
        
        .beacon-container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: shimmer 4s linear infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
            100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
        }
        
        @keyframes containerPulse {
            0%, 100% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.02) rotate(0.5deg); }
        }
        
        .beacon-title {
            font-size: 4em;
            margin-bottom: 30px;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.8);
            animation: titleBounce 2s ease-in-out infinite;
            position: relative;
            z-index: 10;
        }
        
        @keyframes titleBounce {
            0%, 100% { transform: translateY(0px) scale(1); }
            50% { transform: translateY(-10px) scale(1.05); }
        }
        
        .mega-beacon {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            margin: 40px auto;
            background: radial-gradient(circle, #FF6B6B, #FF8E53, #FF6B6B);
            animation: megaPulse 1s ease-in-out infinite;
            box-shadow: 
                0 0 50px rgba(255, 107, 107, 0.8),
                0 0 100px rgba(255, 107, 107, 0.6),
                0 0 150px rgba(255, 107, 107, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 4em;
            position: relative;
            z-index: 10;
        }
        
        @keyframes megaPulse {
            0% { 
                transform: scale(1);
                box-shadow: 
                    0 0 50px rgba(255, 107, 107, 0.8),
                    0 0 100px rgba(255, 107, 107, 0.6),
                    0 0 150px rgba(255, 107, 107, 0.4);
            }
            50% { 
                transform: scale(1.15);
                box-shadow: 
                    0 0 80px rgba(255, 107, 107, 1),
                    0 0 150px rgba(255, 107, 107, 0.8),
                    0 0 250px rgba(255, 107, 107, 0.6);
            }
            100% { 
                transform: scale(1);
                box-shadow: 
                    0 0 50px rgba(255, 107, 107, 0.8),
                    0 0 100px rgba(255, 107, 107, 0.6),
                    0 0 150px rgba(255, 107, 107, 0.4);
            }
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 40px 0;
            position: relative;
            z-index: 10;
        }
        
        .status-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.2), rgba(255,255,255,0.05));
            padding: 30px;
            border-radius: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            transition: all 0.3s ease;
            animation: cardFloat 4s ease-in-out infinite;
        }
        
        .status-card:nth-child(even) {
            animation-delay: -2s;
        }
        
        @keyframes cardFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
        }
        
        .status-card:hover {
            transform: scale(1.05) translateY(-10px);
            background: linear-gradient(135deg, rgba(255,255,255,0.3), rgba(255,255,255,0.1));
        }
        
        .card-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        .card-value {
            font-size: 2.5em;
            margin: 15px 0;
            font-weight: bold;
        }
        
        .card-status {
            font-size: 1.2em;
            margin-top: 15px;
        }
        
        .success { color: #00FF88; text-shadow: 0 0 10px rgba(0, 255, 136, 0.5); }
        .warning { color: #FFD93D; text-shadow: 0 0 10px rgba(255, 217, 61, 0.5); }
        .error { color: #FF6B6B; text-shadow: 0 0 10px rgba(255, 107, 107, 0.5); }
        
        .update-time {
            font-size: 1.2em;
            margin-top: 30px;
            opacity: 0.9;
            animation: timeBlink 2s ease-in-out infinite;
            position: relative;
            z-index: 10;
        }
        
        @keyframes timeBlink {
            0%, 100% { opacity: 0.9; }
            50% { opacity: 0.6; }
        }
        
        .commands {
            margin-top: 40px;
            padding: 30px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            text-align: left;
            position: relative;
            z-index: 10;
        }
        
        .command {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            border-left: 4px solid #00FF88;
            animation: commandGlow 3s ease-in-out infinite;
        }
        
        @keyframes commandGlow {
            0%, 100% { box-shadow: 0 0 5px rgba(0, 255, 136, 0.3); }
            50% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.6); }
        }
    </style>
</head>
<body>
    <div class="beacon-container">
        <h1 class="beacon-title">🚨 FRANK HARDWARE BEACON 🚨</h1>
        
        <div class="mega-beacon" id="megaBeacon">🎛️</div>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="card-title">💾 RAM UPGRADE</div>
                <div class="card-value success" id="ramValue">Checking...</div>
                <div class="card-status" id="ramStatus">Verifying hardware...</div>
            </div>
            
            <div class="status-card">
                <div class="card-title">🧠 CPU STATUS</div>
                <div class="card-value success" id="cpuValue">Scanning...</div>
                <div class="card-status" id="cpuStatus">Detecting processor...</div>
            </div>
            
            <div class="status-card">
                <div class="card-title">💽 EXTERNAL SSD</div>
                <div class="card-value warning" id="ssdValue">Searching...</div>
                <div class="card-status" id="ssdStatus">Checking for 1TB drive...</div>
            </div>
            
            <div class="status-card">
                <div class="card-title">📊 SYSTEM HEALTH</div>
                <div class="card-value success" id="healthValue">Analyzing...</div>
                <div class="card-status" id="healthStatus">Computing health score...</div>
            </div>
        </div>
        
        <div class="commands">
            <h3>🔍 Commands to run on Frank's physical system:</h3>
            <div class="command">lsblk -f | grep -E '(1TB|1000|ssd)'</div>
            <div class="command">df -h | grep -E '(TB|1\\.0T)'</div>
            <div class="command">sudo fdisk -l | grep -i '1000\\|TB'</div>
        </div>
        
        <div class="update-time" id="updateTime">🔄 Starting beacon...</div>
    </div>

    <script>
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update timestamp
                document.getElementById('updateTime').textContent = 
                    `🔄 Last Update: ${new Date(data.timestamp).toLocaleTimeString()}`;
                
                // Update RAM
                if (data.ram) {
                    document.getElementById('ramValue').textContent = `${data.ram.total_gb} GB`;
                    document.getElementById('ramStatus').textContent = data.ram.status;
                    
                    const ramValueEl = document.getElementById('ramValue');
                    if (data.ram.upgrade_detected) {
                        ramValueEl.className = 'card-value success';
                        document.getElementById('megaBeacon').style.background = 
                            'radial-gradient(circle, #00FF88, #00CC6A)';
                    } else {
                        ramValueEl.className = 'card-value warning';
                    }
                }
                
                // Update CPU
                if (data.cpu) {
                    document.getElementById('cpuValue').textContent = `${data.cpu.cores} Cores`;
                    document.getElementById('cpuStatus').textContent = 
                        `${data.cpu.model.substring(0, 30)}... | Usage: ${data.cpu.usage_percent.toFixed(1)}%`;
                }
                
                // Update SSD
                if (data.storage) {
                    const ssdDetected = data.storage.external_ssd_detected;
                    document.getElementById('ssdValue').textContent = ssdDetected ? '✅ Found' : '⚠️ Not Found';
                    document.getElementById('ssdStatus').textContent = data.storage.status;
                    
                    const ssdValueEl = document.getElementById('ssdValue');
                    ssdValueEl.className = ssdDetected ? 'card-value success' : 'card-value warning';
                }
                
                // Update Health
                if (data.overall_health) {
                    document.getElementById('healthValue').textContent = `${data.overall_health.score}%`;
                    document.getElementById('healthStatus').textContent = 
                        `Status: ${data.overall_health.status} | Environment: ${data.environment.type}`;
                }
                
            } catch (error) {
                console.error('Error updating status:', error);
                document.getElementById('updateTime').textContent = '❌ Connection Error';
            }
        }
        
        // Update every 2 seconds
        setInterval(updateStatus, 2000);
        updateStatus(); // Initial load
    </script>
</body>
</html>'''

def start_beacon_server():
    """Start the beacon HTTP server"""
    server = HTTPServer(('localhost', 8082), BeaconHandler)
    print(f"🚨 Frank Hardware Beacon starting on http://localhost:8082")
    print(f"🌐 Opening beacon in your browser...")
    
    # Try to open in browser
    try:
        webbrowser.open('http://localhost:8082')
    except:
        pass
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Beacon stopped")
        server.shutdown()

if __name__ == "__main__":
    print("🚨" * 20)
    print("FRANK HARDWARE VERIFICATION BEACON")
    print("🚨" * 20)
    print()
    start_beacon_server()