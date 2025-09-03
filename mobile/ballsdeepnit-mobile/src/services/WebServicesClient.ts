import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, {AxiosInstance, AxiosResponse} from 'axios';
import {EventEmitter} from 'events';
import {v4 as uuidv4} from 'uuid';
import io, {Socket} from 'socket.io-client';

export interface Plugin {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  version: string;
  category: string;
  config: any;
  lastUpdate: number;
  dependencies: string[];
  permissions: string[];
}

export interface Bot {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'error';
  config: any;
  plugins: string[];
  stats: {
    uptime: number;
    commands: number;
    errors: number;
  };
}

export interface WebServiceEndpoint {
  id: string;
  name: string;
  url: string;
  method: string;
  status: 'online' | 'offline' | 'error';
  responseTime: number;
  lastCheck: number;
}

export interface DashboardData {
  plugins: Plugin[];
  bots: Bot[];
  endpoints: WebServiceEndpoint[];
  stats: {
    totalPlugins: number;
    activePlugins: number;
    totalBots: number;
    runningBots: number;
    systemHealth: number;
    uptime: number;
  };
}

export interface WebServicesConfig {
  baseUrl: string;
  apiKey: string;
  timeout: number;
  retryAttempts: number;
  enableRealtime: boolean;
  socketUrl?: string;
}

class WebServicesClient extends EventEmitter {
  private static instance: WebServicesClient;
  private httpClient: AxiosInstance;
  private socketClient: Socket | null = null;
  private config: WebServicesConfig;
  private isConnected: boolean = false;
  private sessionId: string;

  private constructor() {
    super();
    
    this.sessionId = uuidv4();
    this.config = {
      baseUrl: 'http://localhost:5000',
      apiKey: 'ballsdeepnit-mobile-2024',
      timeout: 10000,
      retryAttempts: 3,
      enableRealtime: true,
      socketUrl: 'http://localhost:5000',
    };

    this.httpClient = axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`,
        'X-Client-Type': 'mobile',
        'X-Session-ID': this.sessionId,
      },
    });

    this.setupHttpInterceptors();
  }

  public static getInstance(): WebServicesClient {
    if (!WebServicesClient.instance) {
      WebServicesClient.instance = new WebServicesClient();
    }
    return WebServicesClient.instance;
  }

  public async initialize(): Promise<boolean> {
    try {
      // Load stored configuration
      await this.loadStoredConfig();
      
      // Update HTTP client with new config
      this.updateHttpClientConfig();
      
      // Test connection
      const connected = await this.testConnection();
      
      if (connected) {
        // Initialize real-time connection if enabled
        if (this.config.enableRealtime) {
          await this.initializeSocketConnection();
        }
        
        this.isConnected = true;
        this.emit('connected', {
          sessionId: this.sessionId,
          timestamp: Date.now(),
        });
      }
      
      return connected;
    } catch (error) {
      console.error('WebServices initialization error:', error);
      this.emit('error', error);
      return false;
    }
  }

  private async loadStoredConfig(): Promise<void> {
    try {
      const storedConfig = await AsyncStorage.getItem('webservices_config');
      if (storedConfig) {
        const parsed = JSON.parse(storedConfig);
        this.config = {...this.config, ...parsed};
      }
    } catch (error) {
      console.warn('Failed to load stored config:', error);
    }
  }

  private updateHttpClientConfig(): void {
    this.httpClient.defaults.baseURL = this.config.baseUrl;
    this.httpClient.defaults.timeout = this.config.timeout;
    this.httpClient.defaults.headers['Authorization'] = `Bearer ${this.config.apiKey}`;
  }

  private setupHttpInterceptors(): void {
    // Request interceptor
    this.httpClient.interceptors.request.use(
      (config) => {
        config.headers['X-Request-ID'] = uuidv4();
        config.headers['X-Timestamp'] = Date.now().toString();
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.httpClient.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          // Handle token refresh if needed
          return this.httpClient(originalRequest);
        }
        
        return Promise.reject(error);
      }
    );
  }

  private async testConnection(): Promise<boolean> {
    try {
      const response = await this.httpClient.get('/api/health');
      return response.status === 200;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }

  private async initializeSocketConnection(): Promise<void> {
    try {
      if (this.socketClient) {
        this.socketClient.disconnect();
      }

      this.socketClient = io(this.config.socketUrl || this.config.baseUrl, {
        auth: {
          token: this.config.apiKey,
          sessionId: this.sessionId,
          clientType: 'mobile',
        },
        transports: ['websocket'],
      });

      this.socketClient.on('connect', () => {
        console.log('Socket connected');
        this.emit('socket_connected');
      });

      this.socketClient.on('disconnect', () => {
        console.log('Socket disconnected');
        this.emit('socket_disconnected');
      });

      this.socketClient.on('plugin_update', (data) => {
        this.emit('plugin_update', data);
      });

      this.socketClient.on('bot_update', (data) => {
        this.emit('bot_update', data);
      });

      this.socketClient.on('system_notification', (data) => {
        this.emit('system_notification', data);
      });

      this.socketClient.on('error', (error) => {
        console.error('Socket error:', error);
        this.emit('socket_error', error);
      });

    } catch (error) {
      console.error('Socket initialization error:', error);
    }
  }

  // Dashboard API methods
  public async getDashboardData(): Promise<DashboardData> {
    try {
      const response = await this.httpClient.get('/api/dashboard');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch dashboard data: ${error}`);
    }
  }

  public async getPlugins(): Promise<Plugin[]> {
    try {
      const response = await this.httpClient.get('/api/plugins');
      return response.data.plugins || [];
    } catch (error) {
      throw new Error(`Failed to fetch plugins: ${error}`);
    }
  }

  public async getPlugin(pluginId: string): Promise<Plugin> {
    try {
      const response = await this.httpClient.get(`/api/plugins/${pluginId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch plugin ${pluginId}: ${error}`);
    }
  }

  public async installPlugin(pluginData: any): Promise<Plugin> {
    try {
      const response = await this.httpClient.post('/api/plugins/install', pluginData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to install plugin: ${error}`);
    }
  }

  public async uninstallPlugin(pluginId: string): Promise<boolean> {
    try {
      await this.httpClient.delete(`/api/plugins/${pluginId}`);
      return true;
    } catch (error) {
      throw new Error(`Failed to uninstall plugin ${pluginId}: ${error}`);
    }
  }

  public async enablePlugin(pluginId: string): Promise<boolean> {
    try {
      await this.httpClient.post(`/api/plugins/${pluginId}/enable`);
      return true;
    } catch (error) {
      throw new Error(`Failed to enable plugin ${pluginId}: ${error}`);
    }
  }

  public async disablePlugin(pluginId: string): Promise<boolean> {
    try {
      await this.httpClient.post(`/api/plugins/${pluginId}/disable`);
      return true;
    } catch (error) {
      throw new Error(`Failed to disable plugin ${pluginId}: ${error}`);
    }
  }

  public async updatePluginConfig(pluginId: string, config: any): Promise<Plugin> {
    try {
      const response = await this.httpClient.put(`/api/plugins/${pluginId}/config`, config);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update plugin config ${pluginId}: ${error}`);
    }
  }

  // Bot management methods
  public async getBots(): Promise<Bot[]> {
    try {
      const response = await this.httpClient.get('/api/bots');
      return response.data.bots || [];
    } catch (error) {
      throw new Error(`Failed to fetch bots: ${error}`);
    }
  }

  public async getBot(botId: string): Promise<Bot> {
    try {
      const response = await this.httpClient.get(`/api/bots/${botId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch bot ${botId}: ${error}`);
    }
  }

  public async createBot(botData: any): Promise<Bot> {
    try {
      const response = await this.httpClient.post('/api/bots', botData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create bot: ${error}`);
    }
  }

  public async startBot(botId: string): Promise<boolean> {
    try {
      await this.httpClient.post(`/api/bots/${botId}/start`);
      return true;
    } catch (error) {
      throw new Error(`Failed to start bot ${botId}: ${error}`);
    }
  }

  public async stopBot(botId: string): Promise<boolean> {
    try {
      await this.httpClient.post(`/api/bots/${botId}/stop`);
      return true;
    } catch (error) {
      throw new Error(`Failed to stop bot ${botId}: ${error}`);
    }
  }

  public async deleteBot(botId: string): Promise<boolean> {
    try {
      await this.httpClient.delete(`/api/bots/${botId}`);
      return true;
    } catch (error) {
      throw new Error(`Failed to delete bot ${botId}: ${error}`);
    }
  }

  // Web service endpoints monitoring
  public async getEndpoints(): Promise<WebServiceEndpoint[]> {
    try {
      const response = await this.httpClient.get('/api/endpoints');
      return response.data.endpoints || [];
    } catch (error) {
      throw new Error(`Failed to fetch endpoints: ${error}`);
    }
  }

  public async pingEndpoint(endpointId: string): Promise<number> {
    try {
      const startTime = Date.now();
      await this.httpClient.get(`/api/endpoints/${endpointId}/ping`);
      return Date.now() - startTime;
    } catch (error) {
      throw new Error(`Failed to ping endpoint ${endpointId}: ${error}`);
    }
  }

  // System control methods
  public async executeCommand(command: string): Promise<any> {
    try {
      const response = await this.httpClient.post('/api/execute', {
        command,
        sessionId: this.sessionId,
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to execute command: ${error}`);
    }
  }

  public async getSystemStats(): Promise<any> {
    try {
      const response = await this.httpClient.get('/api/system/stats');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch system stats: ${error}`);
    }
  }

  public async getSystemLogs(limit: number = 100): Promise<any[]> {
    try {
      const response = await this.httpClient.get(`/api/system/logs?limit=${limit}`);
      return response.data.logs || [];
    } catch (error) {
      throw new Error(`Failed to fetch system logs: ${error}`);
    }
  }

  // File management
  public async uploadFile(file: any, path?: string): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (path) {
        formData.append('path', path);
      }

      const response = await this.httpClient.post('/api/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.path;
    } catch (error) {
      throw new Error(`Failed to upload file: ${error}`);
    }
  }

  public async downloadFile(path: string): Promise<Blob> {
    try {
      const response = await this.httpClient.get(`/api/files/download`, {
        params: {path},
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to download file: ${error}`);
    }
  }

  // Configuration management
  public async updateConfig(newConfig: Partial<WebServicesConfig>): Promise<void> {
    this.config = {...this.config, ...newConfig};
    await AsyncStorage.setItem('webservices_config', JSON.stringify(this.config));
    this.updateHttpClientConfig();
    this.emit('config_updated', this.config);
  }

  public getConfig(): WebServicesConfig {
    return {...this.config};
  }

  public isConnectionActive(): boolean {
    return this.isConnected;
  }

  public async disconnect(): Promise<void> {
    if (this.socketClient) {
      this.socketClient.disconnect();
      this.socketClient = null;
    }
    this.isConnected = false;
    this.emit('disconnected');
  }

  // Real-time subscription methods
  public subscribeToPluginUpdates(): void {
    if (this.socketClient) {
      this.socketClient.emit('subscribe', 'plugin_updates');
    }
  }

  public subscribeToBotUpdates(): void {
    if (this.socketClient) {
      this.socketClient.emit('subscribe', 'bot_updates');
    }
  }

  public subscribeToSystemNotifications(): void {
    if (this.socketClient) {
      this.socketClient.emit('subscribe', 'system_notifications');
    }
  }

  public unsubscribeFromUpdates(type: string): void {
    if (this.socketClient) {
      this.socketClient.emit('unsubscribe', type);
    }
  }
}

export {WebServicesClient};