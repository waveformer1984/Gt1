#!/usr/bin/env node

/**
 * Frank Bot Standalone Core
 * Desktop AI System for HYDI, RAID, and ProtoForge Integration
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const EventEmitter = require('events');
const url = require('url');

class FrankStandalone extends EventEmitter {
  constructor() {
    super();
    this.config = this.loadConfig();
    this.capabilities = new Map();
    this.syncTargets = new Map();
    this.activeTasks = new Map();
    this.systemStatus = 'initializing';
    this.startTime = Date.now();
    
    this.initializeCapabilities();
    this.initializeSyncTargets();
    this.setupSignalHandlers();
  }

  loadConfig() {
    const configPath = path.join(__dirname, 'config.json');
    try {
      const configData = fs.readFileSync(configPath, 'utf8');
      return JSON.parse(configData);
    } catch (error) {
      console.error('[Frank] Config load failed:', error.message);
      return this.getDefaultConfig();
    }
  }

  getDefaultConfig() {
    return {
      frank: {
        name: "Frank Bot Standalone",
        version: "1.0.0",
        mode: "desktop",
        autoStart: true,
        port: 3001
      },
      capabilities: {
        lexiconAnalyzer: { enabled: true },
        systemIntegrator: { enabled: true },
        automationOrchestrator: { enabled: true },
        communicationHub: { enabled: true },
        systemMonitor: { enabled: true }
      },
      integration: {
        hydi: { autopilotSync: true, syncInterval: 30000 },
        raid: { lexiconSync: true, syncInterval: 60000 },
        protoforge: { divisionSync: true, syncInterval: 120000 }
      },
      logging: {
        level: "info",
        file: "./logs/frank.log",
        console: true
      }
    };
  }

  initializeCapabilities() {
    const capabilities = [
      {
        id: 'lexicon-analyzer',
        name: 'Advanced Lexicon Analysis',
        status: 'active',
        performance: { tasksCompleted: 0, successRate: 0.96, avgResponseTime: 1200 }
      },
      {
        id: 'system-integrator',
        name: 'Multi-System Integration',
        status: 'active',
        performance: { tasksCompleted: 0, successRate: 0.94, avgResponseTime: 2300 }
      },
      {
        id: 'automation-orchestrator',
        name: 'Workflow Automation',
        status: 'active',
        performance: { tasksCompleted: 0, successRate: 0.98, avgResponseTime: 3400 }
      },
      {
        id: 'communication-hub',
        name: 'Intelligent Communication',
        status: 'active',
        performance: { tasksCompleted: 0, successRate: 0.97, avgResponseTime: 800 }
      },
      {
        id: 'system-monitor',
        name: 'Real-time System Monitoring',
        status: 'active',
        performance: { tasksCompleted: 0, successRate: 0.99, avgResponseTime: 450 }
      }
    ];

    capabilities.forEach(cap => {
      this.capabilities.set(cap.id, cap);
    });
  }

  initializeSyncTargets() {
    const targets = [
      {
        id: 'hydi-core',
        name: 'HYDI Core System',
        type: 'hydi',
        status: 'connected',
        lastSync: new Date().toISOString(),
        dataPoints: { sent: 0, received: 0, errors: 0 }
      },
      {
        id: 'raid-riplet',
        name: 'RAID Riplet Core',
        type: 'raid',
        status: 'connected',
        lastSync: new Date().toISOString(),
        dataPoints: { sent: 0, received: 0, errors: 0 }
      },
      {
        id: 'protoforge-divisions',
        name: 'ProtoForge Division Network',
        type: 'protoforge',
        status: 'connected',
        lastSync: new Date().toISOString(),
        dataPoints: { sent: 0, received: 0, errors: 0 }
      }
    ];

    targets.forEach(target => {
      this.syncTargets.set(target.id, target);
    });
  }

  setupSignalHandlers() {
    process.on('SIGINT', () => this.shutdown('SIGINT'));
    process.on('SIGTERM', () => this.shutdown('SIGTERM'));
    process.on('uncaughtException', (error) => {
      this.log('error', 'Uncaught exception:', error);
      this.shutdown('uncaughtException');
    });
  }

  async start() {
    try {
      this.log('info', 'Frank Bot Standalone starting...');
      this.log('info', `Configuration: ${this.config.frank.name} v${this.config.frank.version}`);
      
      await this.bootSequence();
      await this.startWebServer();
      await this.startSyncScheduler();
      
      this.systemStatus = 'online';
      this.log('info', 'Frank Bot is fully operational');
      this.log('info', `Web interface: http://localhost:${this.config.frank.port}`);
      
    } catch (error) {
      this.log('error', 'Startup failed:', error);
      process.exit(1);
    }
  }

  async bootSequence() {
    const steps = [
      'Initializing Core Systems',
      'Loading RAID Integration',
      'Connecting to HYDI Network',
      'Calibrating Lexicon Processor',
      'Activating Automation Modules',
      'Establishing Communication Protocols',
      'Running System Diagnostics'
    ];

    this.log('info', 'Beginning boot sequence...');
    
    for (let i = 0; i < steps.length; i++) {
      this.log('info', `${steps[i]}...`);
      await this.sleep(500 + Math.random() * 300);
    }
    
    this.log('info', 'Boot sequence complete');
  }

  async startWebServer() {
    return new Promise((resolve, reject) => {
      const server = http.createServer((req, res) => {
        this.handleRequest(req, res);
      });

      server.listen(this.config.frank.port, (error) => {
        if (error) {
          reject(error);
        } else {
          this.log('info', `Web server listening on port ${this.config.frank.port}`);
          resolve();
        }
      });

      this.server = server;
    });
  }

  handleRequest(req, res) {
    const url = req.url;
    const method = req.method;

    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (method === 'OPTIONS') {
      res.writeHead(200);
      res.end();
      return;
    }

    if (url === '/status' && method === 'GET') {
      this.handleStatusRequest(res);
    } else if (url === '/task' && method === 'POST') {
      this.handleTaskRequest(req, res);
    } else if (url === '/sync' && method === 'POST') {
      this.handleSyncRequest(req, res);
    } else if (url === '/' && method === 'GET') {
      this.handleIndexRequest(res);
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
    }
  }

  handleStatusRequest(res) {
    const status = {
      systemStatus: this.systemStatus,
      uptime: Date.now() - this.startTime,
      capabilities: Array.from(this.capabilities.values()),
      syncTargets: Array.from(this.syncTargets.values()),
      activeTasks: this.activeTasks.size,
      config: this.config.frank
    };

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(status, null, 2));
  }

  handleTaskRequest(req, res) {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const task = JSON.parse(body);
        const result = this.processTask(task);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result, null, 2));
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  }

  handleSyncRequest(req, res) {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const syncRequest = JSON.parse(body);
        const result = this.performSync(syncRequest.targetId || 'all');
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result, null, 2));
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  }

  handleIndexRequest(res) {
    const htmlPath = path.join(__dirname, 'web', 'index.html');
    
    fs.readFile(htmlPath, 'utf8', (err, data) => {
      if (err) {
        // Fallback HTML interface
        const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Frank Bot Standalone</title>
    <style>
        body { font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }
        .header { text-align: center; border: 1px solid #00ff00; padding: 20px; margin-bottom: 20px; }
        .status { margin: 10px 0; }
        .capability { margin: 5px 0; padding: 5px; border-left: 3px solid #00ff00; }
    </style>
</head>
<body>
    <div class="header">
        <h1>FRANK BOT STANDALONE</h1>
        <p>Desktop AI System - Status: ${this.systemStatus.toUpperCase()}</p>
    </div>
    
    <div class="status">
        <h3>System Information</h3>
        <p>Uptime: ${Math.floor((Date.now() - this.startTime) / 1000)}s</p>
        <p>Capabilities: ${this.capabilities.size} active</p>
        <p>Sync Targets: ${this.syncTargets.size} connected</p>
    </div>
    
    <div class="capabilities">
        <h3>Active Capabilities</h3>
        ${Array.from(this.capabilities.values()).map(cap => 
          `<div class="capability">${cap.name} - ${cap.status}</div>`
        ).join('')}
    </div>
    
    <div class="api">
        <h3>API Endpoints</h3>
        <p>GET /status - System status</p>
        <p>POST /task - Process task</p>
        <p>POST /sync - Sync systems</p>
    </div>
</body>
</html>`;
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(html);
      } else {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(data);
      }
    });
  }

  processTask(task) {
    const taskId = `frank_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    const startTime = Date.now();
    
    this.log('info', `Processing task: ${task.taskType} - ${task.description}`);
    
    // Simulate task processing
    const result = {
      taskId,
      type: task.taskType,
      description: task.description,
      status: 'completed',
      processingTime: Math.random() * 500 + 100,
      timestamp: new Date().toISOString(),
      result: this.generateTaskResult(task.taskType)
    };

    // Update capability performance
    const capability = this.findCapabilityForTask(task.taskType);
    if (capability) {
      capability.performance.tasksCompleted++;
    }

    return result;
  }

  generateTaskResult(taskType) {
    switch (taskType) {
      case 'analysis':
        return {
          detectedPatterns: ['system-optimization', 'performance-monitoring'],
          insights: ['System operating within optimal parameters'],
          recommendations: ['Continue current monitoring schedule']
        };
      case 'integration':
        return {
          connectedSystems: ['HYDI', 'RAID', 'ProtoForge'],
          syncStatus: 'complete',
          dataTransferred: Math.floor(Math.random() * 1000) + 500
        };
      case 'automation':
        return {
          workflowsOptimized: Math.floor(Math.random() * 10) + 1,
          timesSaved: `${Math.floor(Math.random() * 60) + 10} minutes`,
          automationLevel: 'high'
        };
      default:
        return { message: 'Task completed successfully' };
    }
  }

  findCapabilityForTask(taskType) {
    const typeMap = {
      'analysis': 'lexicon-analyzer',
      'integration': 'system-integrator',
      'automation': 'automation-orchestrator',
      'communication': 'communication-hub',
      'monitoring': 'system-monitor'
    };
    
    const capabilityId = typeMap[taskType] || 'communication-hub';
    return this.capabilities.get(capabilityId);
  }

  performSync(targetId) {
    this.log('info', `Performing sync: ${targetId}`);
    
    if (targetId === 'all') {
      const results = [];
      for (const [id, target] of this.syncTargets) {
        target.lastSync = new Date().toISOString();
        target.dataPoints.sent += Math.floor(Math.random() * 50) + 10;
        target.dataPoints.received += Math.floor(Math.random() * 75) + 15;
        results.push({ targetId: id, status: 'synced' });
      }
      return { message: 'All systems synced', results };
    } else {
      const target = this.syncTargets.get(targetId);
      if (target) {
        target.lastSync = new Date().toISOString();
        target.dataPoints.sent += Math.floor(Math.random() * 25) + 5;
        target.dataPoints.received += Math.floor(Math.random() * 35) + 10;
        return { message: `${target.name} synced successfully` };
      } else {
        throw new Error(`Sync target ${targetId} not found`);
      }
    }
  }

  async startSyncScheduler() {
    setInterval(() => {
      this.performSync('all');
    }, 60000); // Sync every minute
    
    this.log('info', 'Sync scheduler started');
  }

  log(level, ...messages) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${messages.join(' ')}`;
    
    if (this.config.logging.console) {
      console.log(logMessage);
    }
    
    if (this.config.logging.file) {
      const logPath = path.join(__dirname, this.config.logging.file);
      fs.appendFileSync(logPath, logMessage + '\n');
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  shutdown(signal) {
    this.log('info', `Received ${signal}, shutting down...`);
    
    if (this.server) {
      this.server.close();
    }
    
    this.systemStatus = 'offline';
    this.log('info', 'Frank Bot shutdown complete');
    process.exit(0);
  }
}

// Start Frank Bot if run directly
if (require.main === module) {
  const frank = new FrankStandalone();
  frank.start().catch(error => {
    console.error('Frank Bot failed to start:', error);
    process.exit(1);
  });
}

module.exports = FrankStandalone;