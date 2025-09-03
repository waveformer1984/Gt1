"""
Frank Hardware Verification Beacon
Visual notification system for hardware upgrade verification
"""

import asyncio
import json
import time
from typing import Dict, Any
from datetime import datetime
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from ..utils.logging import get_logger
from .hardware_monitor import frank_hardware

logger = get_logger(__name__)


class HardwareBeacon:
    """Visual beacon for hardware verification"""
    
    def __init__(self):
        self.app = FastAPI(title="Frank Hardware Verification Beacon")
        self.active_connections = []
        self.beacon_data = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Setup beacon routes and WebSocket"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def beacon_page():
            return self.get_beacon_html()
        
        @self.app.websocket("/ws/beacon")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    # Send beacon data every 2 seconds
                    beacon_data = await self.get_beacon_data()
                    await websocket.send_text(json.dumps(beacon_data))
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
        
        @self.app.get("/api/beacon")
        async def get_beacon_api():
            return await self.get_beacon_data()
        
        @self.app.get("/api/verify")
        async def trigger_verification():
            """Trigger immediate hardware verification"""
            hardware_data = await frank_hardware.get_complete_hardware_specs()
            return {
                "status": "verification_triggered",
                "timestamp": datetime.now().isoformat(),
                "hardware": hardware_data
            }
    
    async def get_beacon_data(self) -> Dict[str, Any]:
        """Get current beacon verification data"""
        try:
            hardware_specs = await frank_hardware.get_complete_hardware_specs()
            
            # Extract key verification info
            beacon_data = {
                "timestamp": datetime.now().isoformat(),
                "beacon_status": "ACTIVE",
                "verification": {
                    "ram_upgrade": {
                        "detected": False,
                        "capacity": "Unknown",
                        "status": "Checking..."
                    },
                    "external_ssd": {
                        "detected": False,
                        "capacity": "Unknown", 
                        "status": "Requires host verification"
                    },
                    "environment": {
                        "type": "Container",
                        "access": "Limited"
                    }
                },
                "system_health": {
                    "cpu_usage": 0,
                    "memory_usage": 0,
                    "status": "Good"
                }
            }
            
            # Process memory info
            if 'memory_specs' in hardware_specs:
                memory = hardware_specs['memory_specs']
                total_gb = memory.get('total_gb', 0)
                usage_percent = memory.get('usage_percent', 0)
                
                beacon_data["verification"]["ram_upgrade"] = {
                    "detected": total_gb >= 15,
                    "capacity": f"{total_gb:.1f} GB",
                    "status": "✅ VERIFIED - Upgrade Successful" if total_gb >= 15 else "❌ Not Detected",
                    "utilization": f"{usage_percent:.1f}%"
                }
                
                beacon_data["system_health"]["memory_usage"] = usage_percent
            
            # Process CPU info
            if 'cpu_specs' in hardware_specs:
                cpu = hardware_specs['cpu_specs']
                cpu_usage = cpu.get('current_usage', 0)
                beacon_data["system_health"]["cpu_usage"] = cpu_usage
            
            # Process upgrade analysis
            if 'upgrade_analysis' in hardware_specs:
                analysis = hardware_specs['upgrade_analysis']
                if 'upgrade_status' in analysis:
                    upgrade_status = analysis['upgrade_status']
                    
                    # Update RAM info from upgrade analysis
                    if 'ram_upgrade' in upgrade_status:
                        ram_info = upgrade_status['ram_upgrade']
                        beacon_data["verification"]["ram_upgrade"].update({
                            "detected": ram_info.get('detected', False),
                            "capacity": f"{ram_info.get('capacity_gb', 0):.1f} GB",
                            "status": ram_info.get('status', 'Unknown'),
                            "available": f"{ram_info.get('available_gb', 0):.1f} GB"
                        })
                    
                    # Update environment info
                    if 'environment_info' in upgrade_status:
                        env_info = upgrade_status['environment_info']
                        beacon_data["verification"]["environment"] = {
                            "type": "Docker Container" if env_info.get('container') else "Physical System",
                            "access": env_info.get('hardware_access', 'Unknown'),
                            "virtualized": env_info.get('virtualized', False)
                        }
                
                # Update external device info
                if 'external_devices' in analysis:
                    ext_devices = analysis['external_devices']
                    device_count = ext_devices.get('total_external_devices', 0)
                    beacon_data["verification"]["external_ssd"] = {
                        "detected": device_count > 0,
                        "capacity": "1TB (Expected)" if device_count == 0 else f"{device_count} devices",
                        "status": "✅ Detected" if device_count > 0 else "⚠️ Requires host system verification",
                        "recommendations": ext_devices.get('recommendations', [])
                    }
            
            # Overall health status
            health_score = 90 if beacon_data["verification"]["ram_upgrade"]["detected"] else 75
            beacon_data["system_health"]["status"] = "Excellent" if health_score >= 85 else "Good"
            beacon_data["system_health"]["score"] = health_score
            
            return beacon_data
            
        except Exception as e:
            logger.error(f"Failed to get beacon data: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "beacon_status": "ERROR",
                "error": str(e)
            }
    
    def get_beacon_html(self) -> str:
        """Generate beacon HTML page"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 Frank Hardware Verification Beacon</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: backgroundPulse 4s ease-in-out infinite alternate;
        }
        
        @keyframes backgroundPulse {
            0% { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            100% { background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); }
        }
        
        .beacon-container {
            text-align: center;
            max-width: 800px;
            width: 100%;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            animation: containerFloat 3s ease-in-out infinite alternate;
        }
        
        @keyframes containerFloat {
            0% { transform: translateY(-10px); }
            100% { transform: translateY(10px); }
        }
        
        .beacon-title {
            font-size: 3em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            animation: titlePulse 2s ease-in-out infinite;
        }
        
        @keyframes titlePulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.15);
            margin: 20px 0;
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid #00ff88;
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            transform: scale(1.02);
            background: rgba(255, 255, 255, 0.2);
        }
        
        .status-success {
            border-left-color: #00ff88;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        
        .status-warning {
            border-left-color: #ffaa00;
            box-shadow: 0 0 20px rgba(255, 170, 0, 0.3);
        }
        
        .status-error {
            border-left-color: #ff4757;
            box-shadow: 0 0 20px rgba(255, 71, 87, 0.3);
        }
        
        .status-title {
            font-size: 1.4em;
            margin-bottom: 10px;
            font-weight: bold;
        }
        
        .status-value {
            font-size: 1.8em;
            margin: 10px 0;
            font-weight: bold;
        }
        
        .beacon-indicator {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            margin: 30px auto;
            background: radial-gradient(circle, #00ff88, #00cc6a);
            animation: beaconPulse 1.5s ease-in-out infinite;
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2em;
        }
        
        @keyframes beaconPulse {
            0% { 
                transform: scale(1);
                box-shadow: 0 0 30px rgba(0, 255, 136, 0.6);
            }
            50% { 
                transform: scale(1.1);
                box-shadow: 0 0 50px rgba(0, 255, 136, 0.9);
            }
            100% { 
                transform: scale(1);
                box-shadow: 0 0 30px rgba(0, 255, 136, 0.6);
            }
        }
        
        .timestamp {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 20px;
        }
        
        .health-bar {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .health-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00cc6a);
            transition: width 0.5s ease;
            border-radius: 10px;
        }
        
        .commands-section {
            margin-top: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            text-align: left;
        }
        
        .command {
            background: rgba(0, 0, 0, 0.3);
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            border-left: 3px solid #00ff88;
        }
    </style>
</head>
<body>
    <div class="beacon-container">
        <h1 class="beacon-title">🚨 FRANK HARDWARE BEACON 🚨</h1>
        
        <div class="beacon-indicator" id="beaconIndicator">
            🎛️
        </div>
        
        <div id="ramStatus" class="status-card status-success">
            <div class="status-title">💾 RAM UPGRADE STATUS</div>
            <div class="status-value" id="ramCapacity">Checking...</div>
            <div id="ramDetails">Verifying hardware configuration...</div>
        </div>
        
        <div id="ssdStatus" class="status-card status-warning">
            <div class="status-title">💽 EXTERNAL SSD STATUS</div>
            <div class="status-value" id="ssdCapacity">Scanning...</div>
            <div id="ssdDetails">Checking for external storage...</div>
        </div>
        
        <div id="systemHealth" class="status-card status-success">
            <div class="status-title">📊 SYSTEM HEALTH</div>
            <div class="health-bar">
                <div class="health-fill" id="healthBar" style="width: 85%;"></div>
            </div>
            <div id="healthDetails">System Status: Excellent</div>
        </div>
        
        <div class="commands-section">
            <h3>🔍 Verification Commands for Host System:</h3>
            <div class="command">lsblk -f | grep -E '(1TB|1000|ssd)'</div>
            <div class="command">df -h | grep -E '(TB|1\\.0T)'</div>
            <div class="command">sudo fdisk -l | grep -i '1000\\|TB'</div>
            <div class="command">mount | grep -i external</div>
        </div>
        
        <div class="timestamp" id="timestamp">
            Last Updated: Connecting...
        </div>
    </div>

    <script>
        let socket;
        let reconnectInterval;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/beacon`;
            
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                console.log('Beacon WebSocket connected');
                clearInterval(reconnectInterval);
            };
            
            socket.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    updateBeacon(data);
                } catch (e) {
                    console.error('Error parsing beacon data:', e);
                }
            };
            
            socket.onclose = function(event) {
                console.log('Beacon WebSocket disconnected');
                // Try to reconnect every 3 seconds
                reconnectInterval = setInterval(connectWebSocket, 3000);
            };
            
            socket.onerror = function(error) {
                console.error('Beacon WebSocket error:', error);
            };
        }
        
        function updateBeacon(data) {
            document.getElementById('timestamp').textContent = 
                `Last Updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
            
            // Update RAM status
            if (data.verification && data.verification.ram_upgrade) {
                const ram = data.verification.ram_upgrade;
                const ramCard = document.getElementById('ramStatus');
                
                document.getElementById('ramCapacity').textContent = ram.capacity;
                document.getElementById('ramDetails').textContent = ram.status;
                
                if (ram.detected) {
                    ramCard.className = 'status-card status-success';
                    document.getElementById('beaconIndicator').style.background = 
                        'radial-gradient(circle, #00ff88, #00cc6a)';
                } else {
                    ramCard.className = 'status-card status-warning';
                }
            }
            
            // Update SSD status
            if (data.verification && data.verification.external_ssd) {
                const ssd = data.verification.external_ssd;
                const ssdCard = document.getElementById('ssdStatus');
                
                document.getElementById('ssdCapacity').textContent = ssd.capacity;
                document.getElementById('ssdDetails').textContent = ssd.status;
                
                if (ssd.detected) {
                    ssdCard.className = 'status-card status-success';
                } else {
                    ssdCard.className = 'status-card status-warning';
                }
            }
            
            // Update system health
            if (data.system_health) {
                const health = data.system_health;
                const healthBar = document.getElementById('healthBar');
                const healthDetails = document.getElementById('healthDetails');
                
                healthBar.style.width = `${health.score || 85}%`;
                healthDetails.textContent = 
                    `CPU: ${health.cpu_usage?.toFixed(1) || 0}% | Memory: ${health.memory_usage?.toFixed(1) || 0}% | Status: ${health.status || 'Good'}`;
                
                if (health.score >= 85) {
                    document.getElementById('systemHealth').className = 'status-card status-success';
                } else if (health.score >= 70) {
                    document.getElementById('systemHealth').className = 'status-card status-warning';
                } else {
                    document.getElementById('systemHealth').className = 'status-card status-error';
                }
            }
        }
        
        // Start WebSocket connection
        connectWebSocket();
        
        // Also fetch data via REST API as fallback
        setInterval(async () => {
            try {
                const response = await fetch('/api/beacon');
                const data = await response.json();
                updateBeacon(data);
            } catch (e) {
                console.log('REST API fallback failed:', e);
            }
        }, 5000);
    </script>
</body>
</html>
        """
    
    async def start_beacon(self, host: str = "localhost", port: int = 8081):
        """Start the hardware verification beacon"""
        logger.info(f"🚨 Starting Frank Hardware Verification Beacon")
        logger.info(f"🌐 Beacon URL: http://{host}:{port}")
        logger.info(f"📡 WebSocket: ws://{host}:{port}/ws/beacon")
        logger.info(f"🔧 API: http://{host}:{port}/api/beacon")
        
        try:
            uvicorn.run(self.app, host=host, port=port, log_level="info")
        except Exception as e:
            logger.error(f"Failed to start beacon: {e}")


# Global beacon instance
hardware_beacon = HardwareBeacon()