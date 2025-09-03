import AsyncStorage from '@react-native-async-storage/async-storage';
import {EventEmitter} from 'events';
import {v4 as uuidv4} from 'uuid';
import {Buffer} from 'buffer';
import {BluetoothService} from './BluetoothService';
import {DataStorageService} from './DataStorageService';
import {PrivacyService} from './PrivacyService';

export interface OBD2Parameter {
  pid: string;
  name: string;
  description: string;
  unit: string;
  formula: string;
  min: number;
  max: number;
  category: 'engine' | 'transmission' | 'emissions' | 'fuel' | 'temperature' | 'pressure' | 'other';
}

export interface OBD2Reading {
  id: string;
  timestamp: number;
  sessionId: string;
  vehicleId: string;
  pid: string;
  parameterName: string;
  rawValue: string;
  calculatedValue: number;
  unit: string;
  category: string;
  latitude?: number;
  longitude?: number;
  metadata?: {
    speed?: number;
    rpm?: number;
    temperature?: number;
    [key: string]: any;
  };
}

export interface VehicleInfo {
  vin?: string;
  make?: string;
  model?: string;
  year?: number;
  engine?: string;
  protocols: string[];
  supportedPids: string[];
  ecuCount: number;
}

export interface ScanSession {
  id: string;
  startTime: number;
  endTime?: number;
  vehicleId: string;
  deviceId: string;
  adapterType: 'ELM327' | 'STN1110' | 'Other';
  protocolUsed: string;
  totalReadings: number;
  averageResponseTime: number;
  errors: number;
  researchConsent: boolean;
}

export interface ZareoOBD2Config {
  adapterType: 'ELM327' | 'STN1110' | 'Other';
  protocol: 'AUTO' | 'ISO9141' | 'KWP2000' | 'CAN11' | 'CAN29';
  scanInterval: number;
  enableRealtime: boolean;
  enableLogging: boolean;
  researchMode: boolean;
  privacyLevel: 'minimal' | 'standard' | 'comprehensive';
  autoConnect: boolean;
  selectedPids: string[];
  maxSessionDuration: number;
}

// Standard OBD2 PIDs for research
const RESEARCH_PIDS: OBD2Parameter[] = [
  {
    pid: '01 05',
    name: 'Engine Coolant Temperature',
    description: 'Temperature of engine coolant',
    unit: '°C',
    formula: 'A - 40',
    min: -40,
    max: 215,
    category: 'temperature',
  },
  {
    pid: '01 0C',
    name: 'Engine RPM',
    description: 'Engine revolutions per minute',
    unit: 'rpm',
    formula: '((A*256)+B)/4',
    min: 0,
    max: 16383.75,
    category: 'engine',
  },
  {
    pid: '01 0D',
    name: 'Vehicle Speed',
    description: 'Vehicle speed sensor reading',
    unit: 'km/h',
    formula: 'A',
    min: 0,
    max: 255,
    category: 'other',
  },
  {
    pid: '01 11',
    name: 'Throttle Position',
    description: 'Absolute throttle position',
    unit: '%',
    formula: 'A*100/255',
    min: 0,
    max: 100,
    category: 'engine',
  },
  {
    pid: '01 0F',
    name: 'Intake Air Temperature',
    description: 'Temperature of intake air',
    unit: '°C',
    formula: 'A - 40',
    min: -40,
    max: 215,
    category: 'temperature',
  },
  {
    pid: '01 10',
    name: 'Mass Air Flow',
    description: 'Mass air flow sensor reading',
    unit: 'g/s',
    formula: '((A*256)+B)/100',
    min: 0,
    max: 655.35,
    category: 'engine',
  },
  {
    pid: '01 2F',
    name: 'Fuel Tank Level',
    description: 'Fuel tank level input',
    unit: '%',
    formula: 'A*100/255',
    min: 0,
    max: 100,
    category: 'fuel',
  },
  {
    pid: '01 42',
    name: 'Control Module Voltage',
    description: 'Control module power supply voltage',
    unit: 'V',
    formula: '((A*256)+B)/1000',
    min: 0,
    max: 65.535,
    category: 'other',
  },
];

class ZareoOBD2Service extends EventEmitter {
  private static instance: ZareoOBD2Service;
  private config: ZareoOBD2Config;
  private bluetoothService: BluetoothService;
  private dataStorage: DataStorageService;
  private privacyService: PrivacyService;
  private isConnected: boolean = false;
  private isScanning: boolean = false;
  private currentSession: ScanSession | null = null;
  private connectedDevice: any = null;
  private supportedPids: string[] = [];
  private vehicleInfo: VehicleInfo | null = null;
  private scanIntervalId: NodeJS.Timeout | null = null;

  private constructor() {
    super();
    
    this.config = {
      adapterType: 'ELM327',
      protocol: 'AUTO',
      scanInterval: 1000, // 1 second
      enableRealtime: true,
      enableLogging: true,
      researchMode: true,
      privacyLevel: 'standard',
      autoConnect: false,
      selectedPids: ['01 05', '01 0C', '01 0D', '01 11'], // Basic engine parameters
      maxSessionDuration: 3600000, // 1 hour
    };

    this.bluetoothService = BluetoothService.getInstance();
    this.dataStorage = DataStorageService.getInstance();
    this.privacyService = PrivacyService.getInstance();
  }

  public static getInstance(): ZareoOBD2Service {
    if (!ZareoOBD2Service.instance) {
      ZareoOBD2Service.instance = new ZareoOBD2Service();
    }
    return ZareoOBD2Service.instance;
  }

  public async initialize(): Promise<boolean> {
    try {
      // Load stored configuration
      await this.loadStoredConfig();
      
      // Set up event listeners
      this.setupEventListeners();
      
      this.emit('initialized', {
        supportedPids: this.getSupportedPids(),
        researchMode: this.config.researchMode,
      });
      
      return true;
    } catch (error) {
      console.error('ZareoOBD2Service initialization error:', error);
      this.emit('error', error);
      return false;
    }
  }

  private async loadStoredConfig(): Promise<void> {
    try {
      const storedConfig = await AsyncStorage.getItem('zareo_obd2_config');
      if (storedConfig) {
        const parsed = JSON.parse(storedConfig);
        this.config = {...this.config, ...parsed};
      }
    } catch (error) {
      console.warn('Failed to load stored OBD2 config:', error);
    }
  }

  private setupEventListeners(): void {
    this.bluetoothService.on('device_connected', (device) => {
      if (this.isOBD2Adapter(device)) {
        this.handleAdapterConnected(device);
      }
    });

    this.bluetoothService.on('device_disconnected', (device) => {
      if (device.id === this.connectedDevice?.id) {
        this.handleAdapterDisconnected();
      }
    });

    this.bluetoothService.on('data_received', (data) => {
      this.handleOBD2Response(data);
    });
  }

  private isOBD2Adapter(device: any): boolean {
    const obd2Names = ['elm327', 'obd', 'scan', 'obdii', 'stn1110'];
    const deviceName = device.name?.toLowerCase() || '';
    return obd2Names.some(name => deviceName.includes(name));
  }

  public async connectToAdapter(deviceId: string): Promise<boolean> {
    try {
      const device = await this.bluetoothService.connectToDevice(deviceId);
      if (!device) {
        throw new Error('Failed to connect to OBD2 adapter');
      }

      this.connectedDevice = device;
      
      // Initialize OBD2 connection
      await this.initializeOBD2Connection();
      
      this.isConnected = true;
      this.emit('adapter_connected', {
        device,
        vehicleInfo: this.vehicleInfo,
        supportedPids: this.supportedPids,
      });
      
      return true;
    } catch (error) {
      console.error('Failed to connect to OBD2 adapter:', error);
      this.emit('connection_error', error);
      return false;
    }
  }

  private async initializeOBD2Connection(): Promise<void> {
    try {
      // Reset adapter
      await this.sendCommand('ATZ');
      await this.wait(2000);

      // Turn off echo
      await this.sendCommand('ATE0');
      
      // Set line feeds off
      await this.sendCommand('ATL0');
      
      // Set headers off
      await this.sendCommand('ATH0');
      
      // Set spaces off
      await this.sendCommand('ATS0');
      
      // Set protocol to auto
      if (this.config.protocol === 'AUTO') {
        await this.sendCommand('ATSP0');
      }
      
      // Get vehicle information
      await this.getVehicleInfo();
      
      // Discover supported PIDs
      await this.discoverSupportedPids();
      
    } catch (error) {
      throw new Error(`OBD2 initialization failed: ${error}`);
    }
  }

  private async getVehicleInfo(): Promise<void> {
    try {
      // Try to get VIN
      const vinResponse = await this.sendCommand('0902');
      
      // Get supported PIDs for service 01
      const supportedResponse = await this.sendCommand('0100');
      
      // Get protocol information
      const protocolResponse = await this.sendCommand('ATDPN');
      
      this.vehicleInfo = {
        vin: this.parseVIN(vinResponse),
        protocols: [protocolResponse],
        supportedPids: this.parseSupportedPids(supportedResponse),
        ecuCount: 1, // Will be updated as we discover more
      };
      
    } catch (error) {
      console.warn('Failed to get complete vehicle info:', error);
      this.vehicleInfo = {
        protocols: ['Unknown'],
        supportedPids: [],
        ecuCount: 1,
      };
    }
  }

  private async discoverSupportedPids(): Promise<void> {
    try {
      // Check PIDs 00, 20, 40, 60, 80, A0, C0, E0 for supported parameters
      const pidRanges = ['0100', '0120', '0140', '0160', '0180', '01A0', '01C0', '01E0'];
      const allSupported: string[] = [];
      
      for (const range of pidRanges) {
        try {
          const response = await this.sendCommand(range);
          const supported = this.parseSupportedPids(response);
          allSupported.push(...supported);
        } catch (error) {
          // Some vehicles don't support all ranges
          console.warn(`Failed to check PID range ${range}:`, error);
        }
      }
      
      this.supportedPids = allSupported;
      this.emit('pids_discovered', this.supportedPids);
      
    } catch (error) {
      console.error('PID discovery failed:', error);
    }
  }

  public async startScan(): Promise<boolean> {
    try {
      if (!this.isConnected) {
        throw new Error('OBD2 adapter not connected');
      }

      if (this.isScanning) {
        throw new Error('Scan already in progress');
      }

      // Check research consent
      const hasConsent = await this.privacyService.hasValidConsent();
      if (!hasConsent && this.config.researchMode) {
        throw new Error('Research consent required for data collection');
      }

      // Create new scan session
      this.currentSession = {
        id: uuidv4(),
        startTime: Date.now(),
        vehicleId: this.vehicleInfo?.vin || 'unknown',
        deviceId: this.connectedDevice.id,
        adapterType: this.config.adapterType,
        protocolUsed: this.vehicleInfo?.protocols[0] || 'unknown',
        totalReadings: 0,
        averageResponseTime: 0,
        errors: 0,
        researchConsent: hasConsent,
      };

      this.isScanning = true;
      
      // Start scanning selected PIDs
      this.startPIDScanning();
      
      this.emit('scan_started', this.currentSession);
      
      return true;
    } catch (error) {
      console.error('Failed to start scan:', error);
      this.emit('scan_error', error);
      return false;
    }
  }

  private startPIDScanning(): void {
    if (!this.isScanning || !this.currentSession) return;

    this.scanIntervalId = setInterval(async () => {
      try {
        for (const pid of this.config.selectedPids) {
          if (!this.isScanning) break;
          
          const startTime = Date.now();
          const response = await this.sendCommand(pid);
          const responseTime = Date.now() - startTime;
          
          const reading = this.parseOBD2Reading(pid, response, responseTime);
          if (reading) {
            await this.processReading(reading);
          }
        }
      } catch (error) {
        console.error('Scan cycle error:', error);
        if (this.currentSession) {
          this.currentSession.errors++;
        }
        this.emit('scan_error', error);
      }
    }, this.config.scanInterval);

    // Auto-stop after max duration
    setTimeout(() => {
      if (this.isScanning) {
        this.stopScan();
      }
    }, this.config.maxSessionDuration);
  }

  private parseOBD2Reading(pid: string, response: string, responseTime: number): OBD2Reading | null {
    try {
      const parameter = RESEARCH_PIDS.find(p => p.pid === pid);
      if (!parameter) return null;

      const rawValue = this.extractDataFromResponse(response);
      if (!rawValue) return null;

      const calculatedValue = this.calculateValue(rawValue, parameter.formula);
      
      const reading: OBD2Reading = {
        id: uuidv4(),
        timestamp: Date.now(),
        sessionId: this.currentSession!.id,
        vehicleId: this.vehicleInfo?.vin || 'unknown',
        pid,
        parameterName: parameter.name,
        rawValue,
        calculatedValue,
        unit: parameter.unit,
        category: parameter.category,
        metadata: {
          responseTime,
          adapterType: this.config.adapterType,
        },
      };

      return reading;
    } catch (error) {
      console.error('Failed to parse OBD2 reading:', error);
      return null;
    }
  }

  private extractDataFromResponse(response: string): string | null {
    // Remove spaces and extract data bytes
    const cleanResponse = response.replace(/\s+/g, '');
    
    // Remove echo if present and find data portion
    const dataMatch = cleanResponse.match(/^[0-9A-F]{2,}/);
    return dataMatch ? dataMatch[0] : null;
  }

  private calculateValue(rawHex: string, formula: string): number {
    try {
      // Convert hex to decimal values
      const bytes = [];
      for (let i = 0; i < rawHex.length; i += 2) {
        bytes.push(parseInt(rawHex.substr(i, 2), 16));
      }

      // Replace A, B, C, D in formula with actual byte values
      let calculation = formula;
      calculation = calculation.replace(/A/g, bytes[0]?.toString() || '0');
      calculation = calculation.replace(/B/g, bytes[1]?.toString() || '0');
      calculation = calculation.replace(/C/g, bytes[2]?.toString() || '0');
      calculation = calculation.replace(/D/g, bytes[3]?.toString() || '0');

      // Evaluate the mathematical expression
      return eval(calculation);
    } catch (error) {
      console.error('Value calculation failed:', error);
      return 0;
    }
  }

  private async processReading(reading: OBD2Reading): Promise<void> {
    try {
      // Store reading
      await this.dataStorage.storeOBD2Reading(reading);
      
      // Update session stats
      if (this.currentSession) {
        this.currentSession.totalReadings++;
        
        // Update average response time
        const totalTime = this.currentSession.averageResponseTime * (this.currentSession.totalReadings - 1);
        this.currentSession.averageResponseTime = 
          (totalTime + (reading.metadata?.responseTime || 0)) / this.currentSession.totalReadings;
      }

      // Emit real-time data
      this.emit('reading_received', reading);
      
      // Check for alerts/anomalies
      this.checkReadingAlerts(reading);
      
    } catch (error) {
      console.error('Failed to process reading:', error);
    }
  }

  private checkReadingAlerts(reading: OBD2Reading): void {
    const parameter = RESEARCH_PIDS.find(p => p.pid === reading.pid);
    if (!parameter) return;

    // Check for out-of-range values
    if (reading.calculatedValue < parameter.min || reading.calculatedValue > parameter.max) {
      this.emit('reading_alert', {
        type: 'out_of_range',
        reading,
        message: `${parameter.name} value ${reading.calculatedValue}${parameter.unit} is outside normal range`,
      });
    }

    // Check for rapid changes (basic anomaly detection)
    // This would be enhanced with historical data comparison
  }

  public async stopScan(): Promise<void> {
    try {
      this.isScanning = false;
      
      if (this.scanIntervalId) {
        clearInterval(this.scanIntervalId);
        this.scanIntervalId = null;
      }

      if (this.currentSession) {
        this.currentSession.endTime = Date.now();
        
        // Store session data
        await this.dataStorage.storeScanSession(this.currentSession);
        
        this.emit('scan_stopped', this.currentSession);
        this.currentSession = null;
      }
      
    } catch (error) {
      console.error('Failed to stop scan:', error);
    }
  }

  private async sendCommand(command: string): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!this.connectedDevice) {
        reject(new Error('No device connected'));
        return;
      }

      const timeout = setTimeout(() => {
        reject(new Error('Command timeout'));
      }, 5000);

      const responseHandler = (data: string) => {
        clearTimeout(timeout);
        this.bluetoothService.removeListener('data_received', responseHandler);
        resolve(data);
      };

      this.bluetoothService.on('data_received', responseHandler);
      this.bluetoothService.sendData(command + '\r');
    });
  }

  private handleAdapterConnected(device: any): void {
    this.connectedDevice = device;
    this.emit('adapter_detected', device);
  }

  private handleAdapterDisconnected(): void {
    this.isConnected = false;
    this.stopScan();
    this.connectedDevice = null;
    this.vehicleInfo = null;
    this.supportedPids = [];
    this.emit('adapter_disconnected');
  }

  private handleOBD2Response(data: string): void {
    this.emit('raw_data', data);
  }

  private parseVIN(response: string): string | undefined {
    // Parse VIN from Mode 09, PID 02 response
    try {
      const cleanResponse = response.replace(/\s+/g, '');
      // VIN parsing logic would go here
      return undefined; // Placeholder
    } catch (error) {
      return undefined;
    }
  }

  private parseSupportedPids(response: string): string[] {
    try {
      const cleanResponse = response.replace(/\s+/g, '');
      const supportedPids: string[] = [];
      
      // Parse 32-bit bitmap to determine supported PIDs
      // Implementation would analyze each bit
      
      return supportedPids;
    } catch (error) {
      return [];
    }
  }

  private wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Public methods
  public getSupportedPids(): OBD2Parameter[] {
    return RESEARCH_PIDS.filter(pid => 
      this.supportedPids.includes(pid.pid) || this.config.selectedPids.includes(pid.pid)
    );
  }

  public getVehicleInfo(): VehicleInfo | null {
    return this.vehicleInfo;
  }

  public getCurrentSession(): ScanSession | null {
    return this.currentSession;
  }

  public isConnectedToAdapter(): boolean {
    return this.isConnected;
  }

  public isScanningActive(): boolean {
    return this.isScanning;
  }

  public async updateConfig(newConfig: Partial<ZareoOBD2Config>): Promise<void> {
    this.config = {...this.config, ...newConfig};
    await AsyncStorage.setItem('zareo_obd2_config', JSON.stringify(this.config));
    this.emit('config_updated', this.config);
  }

  public getConfig(): ZareoOBD2Config {
    return {...this.config};
  }

  public async disconnect(): Promise<void> {
    await this.stopScan();
    if (this.connectedDevice) {
      await this.bluetoothService.disconnectDevice(this.connectedDevice.id);
    }
    this.handleAdapterDisconnected();
  }
}

export {ZareoOBD2Service};