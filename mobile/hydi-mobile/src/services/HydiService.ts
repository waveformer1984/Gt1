import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';

export interface HydiModule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  status: 'active' | 'inactive' | 'error' | 'loading';
  type: 'core' | 'experimental';
  lastUpdated: string;
  logs?: string[];
}

export interface SystemStatus {
  cpu: number;
  memory: number;
  connections: number;
  uptime: string;
  activeModules: number;
  errors: number;
  version: string;
}

export interface REPLResponse {
  success: boolean;
  output: string;
  error?: string;
  timestamp: string;
  executionTime: number;
}

export interface VoiceCommand {
  text: string;
  confidence: number;
  action: string;
  parameters?: any;
}

class HydiServiceClass {
  private baseUrl: string = '';
  private wsConnection: WebSocket | null = null;
  private deviceId: string = '';
  private authToken: string = '';
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private isInitialized: boolean = false;
  
  // Event listeners
  private moduleUpdateListeners: Array<(modules: HydiModule[]) => void> = [];
  private systemStatusListeners: Array<(status: SystemStatus) => void> = [];
  private replResponseListeners: Array<(response: REPLResponse) => void> = [];
  private connectionListeners: Array<(connected: boolean) => void> = [];

  async initialize(): Promise<void> {
    try {
      // Load configuration
      await this.loadConfiguration();
      
      // Get device information
      this.deviceId = await DeviceInfo.getUniqueId();
      
      // Connect to Hydi backend
      await this.connectToBackend();
      
      this.isInitialized = true;
      console.log('HydiService initialized successfully');
    } catch (error) {
      console.error('HydiService initialization failed:', error);
      throw error;
    }
  }

  private async loadConfiguration(): Promise<void> {
    try {
      const config = await AsyncStorage.getItem('hydi_config');
      if (config) {
        const parsedConfig = JSON.parse(config);
        this.baseUrl = parsedConfig.baseUrl || 'http://localhost:8000';
        this.authToken = parsedConfig.authToken || '';
      } else {
        // Default configuration
        this.baseUrl = 'http://localhost:8000';
        await this.saveConfiguration();
      }
    } catch (error) {
      console.error('Error loading configuration:', error);
      this.baseUrl = 'http://localhost:8000';
    }
  }

  private async saveConfiguration(): Promise<void> {
    try {
      const config = {
        baseUrl: this.baseUrl,
        authToken: this.authToken,
        deviceId: this.deviceId,
      };
      await AsyncStorage.setItem('hydi_config', JSON.stringify(config));
    } catch (error) {
      console.error('Error saving configuration:', error);
    }
  }

  private async connectToBackend(): Promise<void> {
    try {
      // Test HTTP connection first
      const response = await fetch(`${this.baseUrl}/api/health`);
      if (!response.ok) {
        throw new Error(`HTTP connection failed: ${response.status}`);
      }

      // Establish WebSocket connection
      await this.connectWebSocket();
      
    } catch (error) {
      console.error('Backend connection failed:', error);
      throw error;
    }
  }

  private connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws';
        this.wsConnection = new WebSocket(wsUrl);

        this.wsConnection.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.notifyConnectionListeners(true);
          
          // Send authentication
          this.sendMessage({
            type: 'auth',
            token: this.authToken,
            deviceId: this.deviceId,
          });
          
          resolve();
        };

        this.wsConnection.onmessage = (event) => {
          this.handleWebSocketMessage(event.data);
        };

        this.wsConnection.onclose = () => {
          console.log('WebSocket disconnected');
          this.notifyConnectionListeners(false);
          this.handleDisconnection();
        };

        this.wsConnection.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleWebSocketMessage(data: string): void {
    try {
      const message = JSON.parse(data);
      
      switch (message.type) {
        case 'modules_update':
          this.notifyModuleUpdateListeners(message.data);
          break;
        case 'system_status':
          this.notifySystemStatusListeners(message.data);
          break;
        case 'repl_response':
          this.notifyReplResponseListeners(message.data);
          break;
        case 'notification':
          this.handleNotification(message.data);
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  private handleDisconnection(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => {
        this.connectWebSocket().catch(console.error);
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  private sendMessage(message: any): void {
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }

  // Public API Methods

  async getModules(): Promise<HydiModule[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/modules`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch modules: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching modules:', error);
      throw error;
    }
  }

  async toggleModule(moduleId: string, enabled: boolean): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/modules/${moduleId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`,
        },
        body: JSON.stringify({ enabled }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to toggle module: ${response.status}`);
      }
    } catch (error) {
      console.error('Error toggling module:', error);
      throw error;
    }
  }

  async executeREPLCommand(command: string): Promise<REPLResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/repl/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`,
        },
        body: JSON.stringify({ command }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to execute command: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error executing REPL command:', error);
      throw error;
    }
  }

  async getSystemStatus(): Promise<SystemStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/api/system/status`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch system status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching system status:', error);
      throw error;
    }
  }

  async processVoiceCommand(voiceData: VoiceCommand): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`,
        },
        body: JSON.stringify(voiceData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to process voice command: ${response.status}`);
      }
    } catch (error) {
      console.error('Error processing voice command:', error);
      throw error;
    }
  }

  async updateConfiguration(config: any): Promise<void> {
    this.baseUrl = config.baseUrl || this.baseUrl;
    this.authToken = config.authToken || this.authToken;
    await this.saveConfiguration();
  }

  async applyUserPreferences(preferences: any): Promise<void> {
    // Apply user preferences to the service
    console.log('Applying user preferences:', preferences);
    // Implementation depends on specific preferences
  }

  // Event listener management
  onModuleUpdate(listener: (modules: HydiModule[]) => void): () => void {
    this.moduleUpdateListeners.push(listener);
    return () => {
      const index = this.moduleUpdateListeners.indexOf(listener);
      if (index > -1) {
        this.moduleUpdateListeners.splice(index, 1);
      }
    };
  }

  onSystemStatusUpdate(listener: (status: SystemStatus) => void): () => void {
    this.systemStatusListeners.push(listener);
    return () => {
      const index = this.systemStatusListeners.indexOf(listener);
      if (index > -1) {
        this.systemStatusListeners.splice(index, 1);
      }
    };
  }

  onREPLResponse(listener: (response: REPLResponse) => void): () => void {
    this.replResponseListeners.push(listener);
    return () => {
      const index = this.replResponseListeners.indexOf(listener);
      if (index > -1) {
        this.replResponseListeners.splice(index, 1);
      }
    };
  }

  onConnectionChange(listener: (connected: boolean) => void): () => void {
    this.connectionListeners.push(listener);
    return () => {
      const index = this.connectionListeners.indexOf(listener);
      if (index > -1) {
        this.connectionListeners.splice(index, 1);
      }
    };
  }

  // Private notification methods
  private notifyModuleUpdateListeners(modules: HydiModule[]): void {
    this.moduleUpdateListeners.forEach(listener => listener(modules));
  }

  private notifySystemStatusListeners(status: SystemStatus): void {
    this.systemStatusListeners.forEach(listener => listener(status));
  }

  private notifyReplResponseListeners(response: REPLResponse): void {
    this.replResponseListeners.forEach(listener => listener(response));
  }

  private notifyConnectionListeners(connected: boolean): void {
    this.connectionListeners.forEach(listener => listener(connected));
  }

  private handleNotification(notification: any): void {
    // Handle push notifications
    console.log('Received notification:', notification);
  }

  // Lifecycle methods
  reconnect(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
    }
    this.connectWebSocket().catch(console.error);
  }

  handleBackground(): void {
    // Handle app going to background
    console.log('App going to background');
  }

  cleanup(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
    
    // Clear listeners
    this.moduleUpdateListeners = [];
    this.systemStatusListeners = [];
    this.replResponseListeners = [];
    this.connectionListeners = [];
    
    this.isInitialized = false;
  }

  isConnected(): boolean {
    return this.wsConnection?.readyState === WebSocket.OPEN;
  }

  getConnectionStatus(): string {
    if (!this.wsConnection) return 'disconnected';
    
    switch (this.wsConnection.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  }
}

export const HydiService = new HydiServiceClass();