import AsyncStorage from '@react-native-async-storage/async-storage';
import {EventEmitter} from 'events';
import CryptoJS from 'crypto-js';
import {v4 as uuidv4} from 'uuid';

export interface HydiCommand {
  id: string;
  command: string;
  timestamp: number;
  type: 'shell' | 'python' | 'javascript' | 'hydi' | 'voice';
  context?: any;
  metadata?: {
    voice?: boolean;
    auto?: boolean;
    chainId?: string;
  };
}

export interface HydiResponse {
  id: string;
  commandId: string;
  response: string;
  status: 'success' | 'error' | 'warning' | 'info';
  timestamp: number;
  executionTime: number;
  output?: any;
  error?: string;
}

export interface HydiContext {
  sessionId: string;
  userId: string;
  deviceId: string;
  capabilities: string[];
  memory: Map<string, any>;
  history: HydiCommand[];
  activeChains: string[];
}

export interface HydiConfig {
  serverUrl: string;
  apiKey: string;
  enableVoice: boolean;
  enableAutoComplete: boolean;
  enableMemory: boolean;
  maxHistorySize: number;
  connectionTimeout: number;
}

class HydiService extends EventEmitter {
  private static instance: HydiService;
  private websocket: WebSocket | null = null;
  private config: HydiConfig;
  private context: HydiContext;
  private isConnected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 5000;

  private constructor() {
    super();
    this.config = {
      serverUrl: 'ws://localhost:8765',
      apiKey: 'hydi-mobile-2024',
      enableVoice: true,
      enableAutoComplete: true,
      enableMemory: true,
      maxHistorySize: 1000,
      connectionTimeout: 10000,
    };

    this.context = {
      sessionId: uuidv4(),
      userId: '',
      deviceId: '',
      capabilities: [
        'shell_execution',
        'python_repl',
        'javascript_execution',
        'voice_control',
        'file_management',
        'plugin_management',
        'web_services_integration',
        'ai_assistance',
        'command_chaining',
        'memory_persistence',
      ],
      memory: new Map(),
      history: [],
      activeChains: [],
    };
  }

  public static getInstance(): HydiService {
    if (!HydiService.instance) {
      HydiService.instance = new HydiService();
    }
    return HydiService.instance;
  }

  public async initialize(): Promise<boolean> {
    try {
      // Load stored configuration
      await this.loadStoredConfig();
      
      // Initialize device context
      await this.initializeDeviceContext();
      
      // Connect to Hydi server
      const connected = await this.connect();
      
      if (connected) {
        // Restore session if available
        await this.restoreSession();
        
        // Set up event listeners
        this.setupEventListeners();
        
        this.emit('initialized', {
          sessionId: this.context.sessionId,
          capabilities: this.context.capabilities,
        });
      }
      
      return connected;
    } catch (error) {
      console.error('Hydi initialization error:', error);
      this.emit('error', error);
      return false;
    }
  }

  private async loadStoredConfig(): Promise<void> {
    try {
      const storedConfig = await AsyncStorage.getItem('hydi_config');
      if (storedConfig) {
        const parsed = JSON.parse(storedConfig);
        this.config = {...this.config, ...parsed};
      }
    } catch (error) {
      console.warn('Failed to load stored config:', error);
    }
  }

  private async initializeDeviceContext(): Promise<void> {
    try {
      const deviceId = await AsyncStorage.getItem('device_id') || uuidv4();
      const userId = await AsyncStorage.getItem('user_id') || 'mobile_user';
      
      await AsyncStorage.setItem('device_id', deviceId);
      await AsyncStorage.setItem('user_id', userId);
      
      this.context.deviceId = deviceId;
      this.context.userId = userId;
    } catch (error) {
      console.warn('Failed to initialize device context:', error);
    }
  }

  public async connect(): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        if (this.websocket) {
          this.websocket.close();
        }

        this.websocket = new WebSocket(this.config.serverUrl);

        const timeout = setTimeout(() => {
          if (this.websocket) {
            this.websocket.close();
          }
          resolve(false);
        }, this.config.connectionTimeout);

        this.websocket.onopen = () => {
          clearTimeout(timeout);
          this.isConnected = true;
          this.reconnectAttempts = 0;
          
          // Send handshake
          this.sendHandshake();
          
          this.emit('connected', {
            sessionId: this.context.sessionId,
            timestamp: Date.now(),
          });
          
          resolve(true);
        };

        this.websocket.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.websocket.onclose = (event) => {
          clearTimeout(timeout);
          this.isConnected = false;
          
          this.emit('disconnected', {
            code: event.code,
            reason: event.reason,
            timestamp: Date.now(),
          });
          
          // Attempt reconnection
          this.scheduleReconnect();
          
          if (this.reconnectAttempts === 0) {
            resolve(false);
          }
        };

        this.websocket.onerror = (error) => {
          clearTimeout(timeout);
          console.error('Hydi WebSocket error:', error);
          this.emit('error', error);
          resolve(false);
        };

      } catch (error) {
        console.error('Hydi connection error:', error);
        this.emit('error', error);
        resolve(false);
      }
    });
  }

  private sendHandshake(): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const handshake = {
        type: 'handshake',
        sessionId: this.context.sessionId,
        userId: this.context.userId,
        deviceId: this.context.deviceId,
        capabilities: this.context.capabilities,
        apiKey: this.config.apiKey,
        timestamp: Date.now(),
      };

      this.websocket.send(JSON.stringify(handshake));
    }
  }

  public async executeCommand(command: string, type: HydiCommand['type'] = 'hydi', metadata?: any): Promise<HydiResponse> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected || !this.websocket) {
        reject(new Error('Hydi service not connected'));
        return;
      }

      const hydiCommand: HydiCommand = {
        id: uuidv4(),
        command,
        timestamp: Date.now(),
        type,
        metadata,
      };

      // Add to history
      this.addToHistory(hydiCommand);

      // Set up response handler
      const responseHandler = (response: HydiResponse) => {
        if (response.commandId === hydiCommand.id) {
          this.removeListener('response', responseHandler);
          resolve(response);
        }
      };

      this.on('response', responseHandler);

      // Send command
      try {
        this.websocket.send(JSON.stringify({
          type: 'command',
          ...hydiCommand,
        }));

        // Set timeout
        setTimeout(() => {
          this.removeListener('response', responseHandler);
          reject(new Error('Command execution timeout'));
        }, 30000);

      } catch (error) {
        this.removeListener('response', responseHandler);
        reject(error);
      }
    });
  }

  public async executeVoiceCommand(audioData: string): Promise<HydiResponse> {
    try {
      const command = await this.processVoiceToText(audioData);
      return this.executeCommand(command, 'voice', {voice: true});
    } catch (error) {
      throw new Error(`Voice command failed: ${error}`);
    }
  }

  private async processVoiceToText(audioData: string): Promise<string> {
    // This would integrate with speech recognition service
    // For now, returning placeholder
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve('list plugins'); // Placeholder
      }, 1000);
    });
  }

  public async executeCommandChain(commands: string[]): Promise<HydiResponse[]> {
    const chainId = uuidv4();
    const responses: HydiResponse[] = [];

    this.context.activeChains.push(chainId);

    try {
      for (const command of commands) {
        const response = await this.executeCommand(command, 'hydi', {
          chainId,
          auto: true,
        });
        responses.push(response);

        // Stop chain execution on error
        if (response.status === 'error') {
          break;
        }
      }
    } finally {
      this.context.activeChains = this.context.activeChains.filter(id => id !== chainId);
    }

    return responses;
  }

  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data);

      switch (message.type) {
        case 'response':
          this.emit('response', message as HydiResponse);
          break;
        
        case 'notification':
          this.emit('notification', message);
          break;
        
        case 'memory_update':
          this.handleMemoryUpdate(message);
          break;
        
        case 'context_update':
          this.handleContextUpdate(message);
          break;
        
        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Failed to parse message:', error);
    }
  }

  private handleMemoryUpdate(message: any): void {
    if (this.config.enableMemory && message.key && message.value !== undefined) {
      this.context.memory.set(message.key, message.value);
      this.persistMemory();
    }
  }

  private handleContextUpdate(message: any): void {
    if (message.capabilities) {
      this.context.capabilities = message.capabilities;
    }
    this.emit('context_updated', this.context);
  }

  private addToHistory(command: HydiCommand): void {
    this.context.history.push(command);
    
    // Limit history size
    if (this.context.history.length > this.config.maxHistorySize) {
      this.context.history = this.context.history.slice(-this.config.maxHistorySize);
    }
    
    this.persistHistory();
  }

  private async persistHistory(): Promise<void> {
    try {
      const encryptedHistory = CryptoJS.AES.encrypt(
        JSON.stringify(this.context.history),
        this.context.sessionId
      ).toString();
      
      await AsyncStorage.setItem('hydi_history', encryptedHistory);
    } catch (error) {
      console.warn('Failed to persist history:', error);
    }
  }

  private async persistMemory(): Promise<void> {
    try {
      const memoryObject = Object.fromEntries(this.context.memory);
      const encryptedMemory = CryptoJS.AES.encrypt(
        JSON.stringify(memoryObject),
        this.context.sessionId
      ).toString();
      
      await AsyncStorage.setItem('hydi_memory', encryptedMemory);
    } catch (error) {
      console.warn('Failed to persist memory:', error);
    }
  }

  private async restoreSession(): Promise<void> {
    try {
      // Restore history
      const encryptedHistory = await AsyncStorage.getItem('hydi_history');
      if (encryptedHistory) {
        const decryptedHistory = CryptoJS.AES.decrypt(encryptedHistory, this.context.sessionId).toString(CryptoJS.enc.Utf8);
        this.context.history = JSON.parse(decryptedHistory);
      }

      // Restore memory
      const encryptedMemory = await AsyncStorage.getItem('hydi_memory');
      if (encryptedMemory) {
        const decryptedMemory = CryptoJS.AES.decrypt(encryptedMemory, this.context.sessionId).toString(CryptoJS.enc.Utf8);
        const memoryObject = JSON.parse(decryptedMemory);
        this.context.memory = new Map(Object.entries(memoryObject));
      }
    } catch (error) {
      console.warn('Failed to restore session:', error);
    }
  }

  private setupEventListeners(): void {
    // Handle app state changes
    // This would typically integrate with React Native's AppState
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, this.reconnectInterval * this.reconnectAttempts);
    }
  }

  public getContext(): HydiContext {
    return {...this.context};
  }

  public getConfig(): HydiConfig {
    return {...this.config};
  }

  public async updateConfig(newConfig: Partial<HydiConfig>): Promise<void> {
    this.config = {...this.config, ...newConfig};
    await AsyncStorage.setItem('hydi_config', JSON.stringify(this.config));
    this.emit('config_updated', this.config);
  }

  public isConnectionActive(): boolean {
    return this.isConnected;
  }

  public async disconnect(): Promise<void> {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnected = false;
    await this.persistHistory();
    await this.persistMemory();
  }

  public clearHistory(): void {
    this.context.history = [];
    AsyncStorage.removeItem('hydi_history');
    this.emit('history_cleared');
  }

  public clearMemory(): void {
    this.context.memory.clear();
    AsyncStorage.removeItem('hydi_memory');
    this.emit('memory_cleared');
  }
}

export {HydiService};