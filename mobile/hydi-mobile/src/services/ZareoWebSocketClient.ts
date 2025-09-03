/**
 * Z-areo WebSocket Client for Mobile OBD2 Data Collection
 * =====================================================
 * 
 * Handles real-time communication with the Z-areo OBD2 system backend.
 * Provides data streaming, command execution, and status updates.
 */

export interface MessageData {
  type: string;
  timestamp: number;
  message_id: string;
  data: any;
}

export interface CommandResult {
  success: boolean;
  result?: any;
  error?: string;
}

export class ZareoWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private pendingCommands = new Map<string, { resolve: Function; reject: Function }>();

  // Event handlers
  public onConnect: (() => void) | null = null;
  public onDisconnect: (() => void) | null = null;
  public onDataStream: ((data: MessageData) => void) | null = null;
  public onStatusUpdate: ((data: MessageData) => void) | null = null;
  public onError: ((error: MessageData) => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  /**
   * Connect to the Z-areo OBD2 WebSocket server
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('Connected to Z-areo OBD2 system');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          
          if (this.onConnect) {
            this.onConnect();
          }
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onclose = (event) => {
          console.log('Disconnected from Z-areo OBD2 system', event.code, event.reason);
          this.handleDisconnection();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(new Error('Failed to connect to Z-areo OBD2 system'));
        };

        // Connection timeout
        setTimeout(() => {
          if (!this.isConnected) {
            this.ws?.close();
            reject(new Error('Connection timeout'));
          }
        }, 10000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    this.isConnected = false;
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Subscribe to OBD2 parameter updates
   */
  async subscribeToParameters(parameters: string[], dataRate: number = 1.0): Promise<void> {
    const message = {
      type: 'subscribe',
      parameters,
      data_rate: dataRate,
      timestamp: Date.now()
    };

    await this.sendMessage(message);
  }

  /**
   * Unsubscribe from OBD2 parameter updates
   */
  async unsubscribeFromParameters(parameters: string[]): Promise<void> {
    const message = {
      type: 'unsubscribe',
      parameters,
      timestamp: Date.now()
    };

    await this.sendMessage(message);
  }

  /**
   * Send a command to the OBD2 system
   */
  async sendCommand(command: string, parameters: any = {}, apiKey?: string): Promise<CommandResult> {
    const messageId = this.generateMessageId();
    
    const message = {
      type: 'command',
      command,
      parameters,
      api_key: apiKey || 'zareo-nonprofit-2024',
      message_id: messageId,
      timestamp: Date.now()
    };

    return new Promise((resolve, reject) => {
      // Store the promise handlers
      this.pendingCommands.set(messageId, { resolve, reject });

      // Set timeout for command
      setTimeout(() => {
        if (this.pendingCommands.has(messageId)) {
          this.pendingCommands.delete(messageId);
          reject(new Error('Command timeout'));
        }
      }, 30000); // 30 second timeout

      // Send the message
      this.sendMessage(message).catch(reject);
    });
  }

  /**
   * Send heartbeat to keep connection alive
   */
  private sendHeartbeat(): void {
    if (!this.isConnected || !this.ws) return;

    const message = {
      type: 'heartbeat',
      timestamp: Date.now()
    };

    this.sendMessage(message).catch((error) => {
      console.error('Failed to send heartbeat:', error);
    });
  }

  /**
   * Start heartbeat interval
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, 30000); // Send heartbeat every 30 seconds
  }

  /**
   * Stop heartbeat interval
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Send a message to the WebSocket server
   */
  private async sendMessage(message: any): Promise<void> {
    if (!this.isConnected || !this.ws) {
      throw new Error('Not connected to server');
    }

    try {
      const messageStr = JSON.stringify(message);
      this.ws.send(messageStr);
    } catch (error) {
      throw new Error('Failed to send message');
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(messageStr: string): void {
    try {
      const message: MessageData = JSON.parse(messageStr);

      switch (message.type) {
        case 'data_stream':
          if (this.onDataStream) {
            this.onDataStream(message);
          }
          break;

        case 'status_update':
          if (this.onStatusUpdate) {
            this.onStatusUpdate(message);
          }
          break;

        case 'command':
          this.handleCommandResponse(message);
          break;

        case 'error':
          if (this.onError) {
            this.onError(message);
          }
          break;

        case 'heartbeat':
          // Heartbeat response - connection is alive
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Failed to parse message:', error);
    }
  }

  /**
   * Handle command responses
   */
  private handleCommandResponse(message: MessageData): void {
    const messageId = message.message_id;
    
    if (this.pendingCommands.has(messageId)) {
      const { resolve } = this.pendingCommands.get(messageId)!;
      this.pendingCommands.delete(messageId);
      resolve(message.data);
    }
  }

  /**
   * Handle disconnection and attempt reconnection
   */
  private handleDisconnection(): void {
    this.isConnected = false;
    this.stopHeartbeat();

    // Reject all pending commands
    this.pendingCommands.forEach(({ reject }) => {
      reject(new Error('Connection lost'));
    });
    this.pendingCommands.clear();

    if (this.onDisconnect) {
      this.onDisconnect();
    }

    // Attempt reconnection
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.attemptReconnection();
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
    }
  }

  /**
   * Attempt to reconnect to the server
   */
  private async attemptReconnection(): Promise<void> {
    if (this.isConnected) return;

    this.reconnectAttempts++;
    console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);

    try {
      await this.connect();
      console.log('Reconnected successfully');
    } catch (error) {
      console.error('Reconnection failed:', error);
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
      }
    }
  }

  /**
   * Generate unique message ID
   */
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get connection status
   */
  public getConnectionStatus(): { connected: boolean; attempts: number } {
    return {
      connected: this.isConnected,
      attempts: this.reconnectAttempts
    };
  }

  /**
   * Set maximum reconnection attempts
   */
  public setMaxReconnectAttempts(attempts: number): void {
    this.maxReconnectAttempts = attempts;
  }

  /**
   * Set reconnection delay
   */
  public setReconnectDelay(delay: number): void {
    this.reconnectDelay = delay;
  }
}