import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { Ionicons } from '@expo/vector-icons';

import { ZareoWebSocketClient } from '../services/ZareoWebSocketClient';
import { OBD2DataService } from '../services/OBD2DataService';
import { DiagnosticCodeCard } from './DiagnosticCodeCard';
import { ParameterMonitor } from './ParameterMonitor';
import { CANMessageViewer } from './CANMessageViewer';

interface VehicleData {
  parameter: string;
  value: number;
  unit: string;
  timestamp: number;
}

interface DiagnosticCode {
  code: string;
  description: string;
  status: string;
  detected_at: string;
}

interface SystemStatus {
  system_running: boolean;
  current_session: string | null;
  components: {
    obd2: any;
    scanner: any;
    can_sniffer: any;
  };
}

const { width: screenWidth } = Dimensions.get('window');

export const OBD2Scanner: React.FC = () => {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  
  // Data state
  const [vehicleData, setVehicleData] = useState<Map<string, VehicleData>>(new Map());
  const [diagnosticCodes, setDiagnosticCodes] = useState<DiagnosticCode[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  
  // UI state
  const [activeTab, setActiveTab] = useState<'dashboard' | 'diagnostics' | 'can' | 'settings'>('dashboard');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [selectedParameters, setSelectedParameters] = useState<string[]>([
    'RPM', 'SPEED', 'THROTTLE_POS', 'ENGINE_LOAD', 'COOLANT_TEMP'
  ]);
  
  // Services
  const wsClient = useRef<ZareoWebSocketClient | null>(null);
  const dataService = useRef<OBD2DataService | null>(null);
  
  // Chart data
  const [chartData, setChartData] = useState<{[key: string]: number[]}>({});
  const [chartLabels, setChartLabels] = useState<string[]>([]);

  useEffect(() => {
    initializeServices();
    return () => {
      disconnect();
    };
  }, []);

  const initializeServices = () => {
    // Initialize WebSocket client
    wsClient.current = new ZareoWebSocketClient('ws://localhost:8765');
    
    // Initialize data service
    dataService.current = new OBD2DataService('http://localhost:8765/api');
    
    // Setup WebSocket event handlers
    if (wsClient.current) {
      wsClient.current.onConnect = () => {
        setIsConnected(true);
        setIsConnecting(false);
        fetchSystemStatus();
      };
      
      wsClient.current.onDisconnect = () => {
        setIsConnected(false);
        setIsMonitoring(false);
      };
      
      wsClient.current.onDataStream = handleDataStream;
      wsClient.current.onStatusUpdate = handleStatusUpdate;
      wsClient.current.onError = handleError;
    }
  };

  const connect = async () => {
    if (!wsClient.current || isConnecting) return;
    
    setIsConnecting(true);
    try {
      await wsClient.current.connect();
    } catch (error) {
      setIsConnecting(false);
      Alert.alert('Connection Error', 'Failed to connect to OBD2 system');
    }
  };

  const disconnect = () => {
    if (wsClient.current) {
      wsClient.current.disconnect();
    }
    setIsConnected(false);
    setIsMonitoring(false);
  };

  const fetchSystemStatus = async () => {
    if (!dataService.current) return;
    
    try {
      const status = await dataService.current.getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const handleDataStream = (data: any) => {
    const newVehicleData = new Map(vehicleData);
    const newChartData = { ...chartData };
    const currentTime = new Date().toLocaleTimeString();
    
    // Update vehicle data
    Object.entries(data.data).forEach(([parameter, paramData]: [string, any]) => {
      if (paramData && typeof paramData === 'object' && 'value' in paramData) {
        newVehicleData.set(parameter, {
          parameter,
          value: paramData.value,
          unit: paramData.unit || '',
          timestamp: paramData.timestamp || Date.now()
        });
        
        // Update chart data
        if (selectedParameters.includes(parameter)) {
          if (!newChartData[parameter]) {
            newChartData[parameter] = [];
          }
          newChartData[parameter].push(paramData.value);
          
          // Keep only last 20 data points
          if (newChartData[parameter].length > 20) {
            newChartData[parameter] = newChartData[parameter].slice(-20);
          }
        }
      }
    });
    
    setVehicleData(newVehicleData);
    setChartData(newChartData);
    
    // Update chart labels
    const newLabels = [...chartLabels, currentTime];
    if (newLabels.length > 20) {
      newLabels.splice(0, newLabels.length - 20);
    }
    setChartLabels(newLabels);
  };

  const handleStatusUpdate = (data: any) => {
    console.log('Status update:', data);
    if (data.data.status === 'connected') {
      fetchSystemStatus();
    }
  };

  const handleError = (error: any) => {
    console.error('WebSocket error:', error);
    Alert.alert('Error', error.data?.error || 'An error occurred');
  };

  const startMonitoring = async () => {
    if (!wsClient.current || !isConnected) return;
    
    try {
      await wsClient.current.subscribeToParameters(selectedParameters, 2.0); // 2 Hz
      setIsMonitoring(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to start monitoring');
    }
  };

  const stopMonitoring = async () => {
    if (!wsClient.current) return;
    
    try {
      await wsClient.current.unsubscribeFromParameters(selectedParameters);
      setIsMonitoring(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to stop monitoring');
    }
  };

  const readDiagnosticCodes = async () => {
    if (!wsClient.current || !isConnected) return;
    
    try {
      const result = await wsClient.current.sendCommand('read_codes', {});
      if (result.success) {
        setDiagnosticCodes(result.codes || []);
      } else {
        Alert.alert('Error', result.error || 'Failed to read diagnostic codes');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to read diagnostic codes');
    }
  };

  const clearDiagnosticCodes = async () => {
    Alert.alert(
      'Clear Diagnostic Codes',
      'Are you sure you want to clear all diagnostic codes?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            if (!wsClient.current || !isConnected) return;
            
            try {
              const result = await wsClient.current.sendCommand('clear_codes', {});
              if (result.success) {
                setDiagnosticCodes([]);
                Alert.alert('Success', 'Diagnostic codes cleared');
              } else {
                Alert.alert('Error', result.error || 'Failed to clear codes');
              }
            } catch (error) {
              Alert.alert('Error', 'Failed to clear diagnostic codes');
            }
          }
        }
      ]
    );
  };

  const performActuatorTest = async (actuator: string, parameters: any) => {
    if (!wsClient.current || !isConnected) return;
    
    try {
      const result = await wsClient.current.sendCommand('actuator_test', {
        actuator,
        test_parameters: parameters
      });
      
      if (result.success) {
        Alert.alert('Test Complete', `${actuator} test completed successfully`);
      } else {
        Alert.alert('Test Failed', result.error || 'Actuator test failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to perform actuator test');
    }
  };

  const renderDashboard = () => (
    <ScrollView style={styles.tabContent}>
      {/* System Status */}
      <View style={styles.statusCard}>
        <Text style={styles.cardTitle}>System Status</Text>
        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>Connection:</Text>
          <Text style={[styles.statusValue, { color: isConnected ? '#4CAF50' : '#F44336' }]}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Text>
        </View>
        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>Monitoring:</Text>
          <Text style={[styles.statusValue, { color: isMonitoring ? '#4CAF50' : '#FF9800' }]}>
            {isMonitoring ? 'Active' : 'Inactive'}
          </Text>
        </View>
        {systemStatus && (
          <View style={styles.statusRow}>
            <Text style={styles.statusLabel}>Session:</Text>
            <Text style={styles.statusValue}>
              {systemStatus.current_session || 'None'}
            </Text>
          </View>
        )}
      </View>

      {/* Vehicle Parameters */}
      <View style={styles.parametersCard}>
        <Text style={styles.cardTitle}>Vehicle Parameters</Text>
        {selectedParameters.map((param) => {
          const data = vehicleData.get(param);
          return (
            <ParameterMonitor
              key={param}
              parameter={param}
              value={data?.value}
              unit={data?.unit}
              timestamp={data?.timestamp}
            />
          );
        })}
      </View>

      {/* Charts */}
      {chartLabels.length > 0 && (
        <View style={styles.chartCard}>
          <Text style={styles.cardTitle}>Real-time Data</Text>
          {selectedParameters.map((param) => {
            const data = chartData[param];
            if (!data || data.length === 0) return null;
            
            return (
              <View key={param} style={styles.chartContainer}>
                <Text style={styles.chartTitle}>{param}</Text>
                <LineChart
                  data={{
                    labels: chartLabels,
                    datasets: [{ data }]
                  }}
                  width={screenWidth - 40}
                  height={220}
                  chartConfig={{
                    backgroundColor: '#ffffff',
                    backgroundGradientFrom: '#ffffff',
                    backgroundGradientTo: '#ffffff',
                    decimalPlaces: 1,
                    color: (opacity = 1) => `rgba(63, 81, 181, ${opacity})`,
                    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                    style: { borderRadius: 16 },
                    propsForDots: {
                      r: '4',
                      strokeWidth: '2',
                      stroke: '#3F51B5'
                    }
                  }}
                  bezier
                  style={styles.chart}
                />
              </View>
            );
          })}
        </View>
      )}
    </ScrollView>
  );

  const renderDiagnostics = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.diagnosticsHeader}>
        <Text style={styles.cardTitle}>Diagnostic Codes</Text>
        <View style={styles.diagnosticsButtons}>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={readDiagnosticCodes}
          >
            <Text style={styles.buttonText}>Read Codes</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.dangerButton]}
            onPress={clearDiagnosticCodes}
          >
            <Text style={styles.buttonText}>Clear Codes</Text>
          </TouchableOpacity>
        </View>
      </View>

      {diagnosticCodes.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="checkmark-circle" size={64} color="#4CAF50" />
          <Text style={styles.emptyStateText}>No diagnostic codes found</Text>
        </View>
      ) : (
        diagnosticCodes.map((code, index) => (
          <DiagnosticCodeCard key={index} code={code} />
        ))
      )}

      {/* Actuator Tests */}
      <View style={styles.actuatorSection}>
        <Text style={styles.cardTitle}>Actuator Tests</Text>
        <Text style={styles.warningText}>
          ⚠️ Use with caution - these tests control vehicle actuators
        </Text>
        
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={() => performActuatorTest('fuel_injector', { pulse_width: 1000 })}
        >
          <Text style={styles.buttonText}>Test Fuel Injector</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={() => performActuatorTest('egr_valve', { position: 50 })}
        >
          <Text style={styles.buttonText}>Test EGR Valve</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderCAN = () => (
    <ScrollView style={styles.tabContent}>
      <CANMessageViewer websocketClient={wsClient.current} />
    </ScrollView>
  );

  const renderSettings = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.settingsCard}>
        <Text style={styles.cardTitle}>Connection Settings</Text>
        
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>Auto-connect on startup</Text>
          {/* Add switch component */}
        </View>
        
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>Data collection consent</Text>
          {/* Add consent management */}
        </View>
      </View>

      <View style={styles.settingsCard}>
        <Text style={styles.cardTitle}>Privacy & Compliance</Text>
        <Text style={styles.privacyText}>
          This app is developed by Z-areo Non-Profit for research purposes.
          All data is collected in accordance with privacy regulations and
          research ethics guidelines.
        </Text>
        
        <TouchableOpacity style={[styles.button, styles.primaryButton]}>
          <Text style={styles.buttonText}>View Privacy Policy</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={[styles.button, styles.secondaryButton]}>
          <Text style={styles.buttonText}>Manage Consent</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Z-areo OBD2 Scanner</Text>
        <View style={styles.headerButtons}>
          {!isConnected ? (
            <TouchableOpacity
              style={[styles.connectButton, isConnecting && styles.connectingButton]}
              onPress={connect}
              disabled={isConnecting}
            >
              {isConnecting ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.connectButtonText}>Connect</Text>
              )}
            </TouchableOpacity>
          ) : (
            <View style={styles.connectedActions}>
              <TouchableOpacity
                style={[styles.monitorButton, isMonitoring && styles.monitoringButton]}
                onPress={isMonitoring ? stopMonitoring : startMonitoring}
              >
                <Text style={styles.monitorButtonText}>
                  {isMonitoring ? 'Stop' : 'Start'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.disconnectButton}
                onPress={disconnect}
              >
                <Text style={styles.disconnectButtonText}>Disconnect</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabBar}>
        {[
          { key: 'dashboard', icon: 'speedometer-outline', label: 'Dashboard' },
          { key: 'diagnostics', icon: 'bug-outline', label: 'Diagnostics' },
          { key: 'can', icon: 'analytics-outline', label: 'CAN' },
          { key: 'settings', icon: 'settings-outline', label: 'Settings' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.activeTab]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Ionicons
              name={tab.icon as any}
              size={24}
              color={activeTab === tab.key ? '#3F51B5' : '#666'}
            />
            <Text
              style={[
                styles.tabLabel,
                activeTab === tab.key && styles.activeTabLabel
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tab Content */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'diagnostics' && renderDiagnostics()}
      {activeTab === 'can' && renderCAN()}
      {activeTab === 'settings' && renderSettings()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#3F51B5',
    padding: 16,
    paddingTop: 50,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  connectingButton: {
    backgroundColor: '#FF9800',
  },
  connectButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  connectedActions: {
    flexDirection: 'row',
    gap: 8,
  },
  monitorButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  monitoringButton: {
    backgroundColor: '#F44336',
  },
  monitorButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  disconnectButton: {
    backgroundColor: '#F44336',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  disconnectButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3F51B5',
  },
  tabLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  activeTabLabel: {
    color: '#3F51B5',
    fontWeight: 'bold',
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  statusCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333',
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusLabel: {
    fontSize: 14,
    color: '#666',
  },
  statusValue: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  parametersCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  chartCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  chartContainer: {
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  chart: {
    borderRadius: 8,
  },
  diagnosticsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  diagnosticsButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  button: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#3F51B5',
  },
  secondaryButton: {
    backgroundColor: '#FF9800',
    marginBottom: 8,
  },
  dangerButton: {
    backgroundColor: '#F44336',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  emptyState: {
    alignItems: 'center',
    padding: 32,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
    marginTop: 8,
  },
  actuatorSection: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginTop: 16,
    elevation: 2,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  warningText: {
    color: '#FF9800',
    fontSize: 14,
    marginBottom: 16,
    textAlign: 'center',
  },
  settingsCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  privacyText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 16,
  },
});