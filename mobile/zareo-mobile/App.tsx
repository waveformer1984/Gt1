import React, {useEffect, useState} from 'react';
import {
  SafeAreaView,
  StatusBar,
  StyleSheet,
  useColorScheme,
  Alert,
  PermissionsAndroid,
  Platform,
  Text,
  View,
} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createDrawerNavigator} from '@react-navigation/drawer';
import {PaperProvider} from 'react-native-paper';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Toast from 'react-native-toast-message';
import {enableScreens} from 'react-native-screens';
import KeepAwake from 'react-native-keep-awake';

// Enable screens optimization
enableScreens();

// Screens
import ScannerScreen from './src/screens/ScannerScreen';
import DataVisualizationScreen from './src/screens/DataVisualizationScreen';
import ResearchDataScreen from './src/screens/ResearchDataScreen';
import HydiConsoleScreen from './src/screens/HydiConsoleScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import BluetoothDevicesScreen from './src/screens/BluetoothDevicesScreen';
import PrivacyComplianceScreen from './src/screens/PrivacyComplianceScreen';
import DataExportScreen from './src/screens/DataExportScreen';
import VehicleProfileScreen from './src/screens/VehicleProfileScreen';

// Services
import {ZareoOBD2Service} from './src/services/ZareoOBD2Service';
import {HydiZareoService} from './src/services/HydiZareoService';
import {BluetoothService} from './src/services/BluetoothService';
import {DataStorageService} from './src/services/DataStorageService';
import {PrivacyService} from './src/services/PrivacyService';

// Context
import {ZareoProvider} from './src/context/ZareoContext';
import {OBD2Provider} from './src/context/OBD2Context';

// Theme
import {zareoLightTheme, zareoDarkTheme} from './src/theme/zareoTheme';

const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();

interface AppState {
  isInitialized: boolean;
  obd2Connected: boolean;
  hydiConnected: boolean;
  bluetoothEnabled: boolean;
  privacyConsent: boolean;
  error: string | null;
}

const LoadingScreen = () => (
  <View style={styles.loadingContainer}>
    <Icon name="settings-bluetooth" size={64} color="#2196F3" />
    <Text style={styles.loadingTitle}>Z-AREO Mobile</Text>
    <Text style={styles.loadingSubtitle}>Initializing OBD2 Research System...</Text>
  </View>
);

const TabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName = '';

          switch (route.name) {
            case 'Scanner':
              iconName = 'scanner';
              break;
            case 'DataViz':
              iconName = 'timeline';
              break;
            case 'Research':
              iconName = 'science';
              break;
            case 'Hydi':
              iconName = 'psychology';
              break;
            case 'Settings':
              iconName = 'settings';
              break;
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#2196F3',
        tabBarInactiveTintColor: '#757575',
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopWidth: 1,
          borderTopColor: '#E0E0E0',
          height: 65,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
      })}>
      <Tab.Screen 
        name="Scanner" 
        component={ScannerScreen}
        options={{title: 'OBD2 Scan'}}
      />
      <Tab.Screen 
        name="DataViz" 
        component={DataVisualizationScreen}
        options={{title: 'Data'}}
      />
      <Tab.Screen 
        name="Research" 
        component={ResearchDataScreen}
        options={{title: 'Research'}}
      />
      <Tab.Screen 
        name="Hydi" 
        component={HydiConsoleScreen}
        options={{title: 'Hydi AI'}}
      />
      <Tab.Screen 
        name="Settings" 
        component={SettingsScreen}
        options={{title: 'Settings'}}
      />
    </Tab.Navigator>
  );
};

const DrawerNavigator = () => {
  return (
    <Drawer.Navigator
      screenOptions={{
        drawerStyle: {
          backgroundColor: '#FFFFFF',
          width: 300,
        },
        drawerActiveTintColor: '#2196F3',
        drawerInactiveTintColor: '#757575',
        headerStyle: {
          backgroundColor: '#2196F3',
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}>
      <Drawer.Screen 
        name="MainTabs" 
        component={TabNavigator}
        options={{
          title: 'Z-AREO Mobile Research',
          drawerIcon: ({color}) => <Icon name="home" size={24} color={color} />,
        }}
      />
      <Drawer.Screen 
        name="BluetoothDevices" 
        component={BluetoothDevicesScreen}
        options={{
          title: 'Bluetooth Devices',
          drawerIcon: ({color}) => <Icon name="bluetooth" size={24} color={color} />,
        }}
      />
      <Drawer.Screen 
        name="VehicleProfile" 
        component={VehicleProfileScreen}
        options={{
          title: 'Vehicle Profile',
          drawerIcon: ({color}) => <Icon name="directions-car" size={24} color={color} />,
        }}
      />
      <Drawer.Screen 
        name="DataExport" 
        component={DataExportScreen}
        options={{
          title: 'Export Research Data',
          drawerIcon: ({color}) => <Icon name="file-download" size={24} color={color} />,
        }}
      />
      <Drawer.Screen 
        name="PrivacyCompliance" 
        component={PrivacyComplianceScreen}
        options={{
          title: 'Privacy & Compliance',
          drawerIcon: ({color}) => <Icon name="privacy-tip" size={24} color={color} />,
        }}
      />
    </Drawer.Navigator>
  );
};

const App: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const [appState, setAppState] = useState<AppState>({
    isInitialized: false,
    obd2Connected: false,
    hydiConnected: false,
    bluetoothEnabled: false,
    privacyConsent: false,
    error: null,
  });

  useEffect(() => {
    initializeApp();
    
    // Keep screen awake during OBD2 scanning
    KeepAwake.activate();
    
    return () => {
      KeepAwake.deactivate();
    };
  }, []);

  const requestPermissions = async (): Promise<boolean> => {
    if (Platform.OS === 'android') {
      try {
        const permissions = [
          PermissionsAndroid.PERMISSIONS.BLUETOOTH,
          PermissionsAndroid.PERMISSIONS.BLUETOOTH_ADMIN,
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          PermissionsAndroid.PERMISSIONS.ACCESS_COARSE_LOCATION,
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.CAMERA,
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        ];

        // Request Bluetooth Scan and Connect permissions for Android 12+
        if (Platform.Version >= 31) {
          permissions.push(
            'android.permission.BLUETOOTH_SCAN',
            'android.permission.BLUETOOTH_CONNECT'
          );
        }

        const granted = await PermissionsAndroid.requestMultiple(permissions);
        
        const allGranted = Object.values(granted).every(
          permission => permission === PermissionsAndroid.RESULTS.GRANTED
        );

        if (!allGranted) {
          Alert.alert(
            'Permissions Required',
            'Z-AREO requires Bluetooth and location permissions for OBD2 scanning. Some features may not work without these permissions.',
            [{text: 'OK', onPress: () => {}}]
          );
          return false;
        }

        return true;
      } catch (err) {
        console.warn('Permission request error:', err);
        return false;
      }
    }
    return true;
  };

  const checkPrivacyConsent = async (): Promise<boolean> => {
    try {
      const privacyService = PrivacyService.getInstance();
      const hasConsent = await privacyService.hasValidConsent();
      
      if (!hasConsent) {
        return new Promise((resolve) => {
          Alert.alert(
            'Research Data Collection Consent',
            'Z-AREO is a non-profit research organization. We collect vehicle diagnostic data for automotive research purposes only. Your data will be anonymized and used exclusively for non-commercial research.\n\nDo you consent to participate in this research?',
            [
              {
                text: 'Decline',
                style: 'cancel',
                onPress: () => resolve(false),
              },
              {
                text: 'View Privacy Policy',
                onPress: () => {
                  // Navigate to privacy policy
                  resolve(false);
                },
              },
              {
                text: 'I Consent',
                onPress: async () => {
                  await privacyService.recordConsent();
                  resolve(true);
                },
              },
            ]
          );
        });
      }
      
      return true;
    } catch (error) {
      console.error('Privacy consent check error:', error);
      return false;
    }
  };

  const initializeApp = async () => {
    try {
      setAppState(prev => ({...prev, error: null}));

      // Request permissions
      const permissionsGranted = await requestPermissions();
      if (!permissionsGranted) {
        throw new Error('Required permissions not granted');
      }

      // Check privacy consent
      const privacyConsent = await checkPrivacyConsent();
      if (!privacyConsent) {
        throw new Error('Privacy consent required for research participation');
      }

      // Initialize data storage service
      const dataStorage = DataStorageService.getInstance();
      await dataStorage.initialize();

      // Initialize Bluetooth service
      const bluetoothService = BluetoothService.getInstance();
      const bluetoothEnabled = await bluetoothService.initialize();

      // Initialize Hydi service
      const hydiService = HydiZareoService.getInstance();
      const hydiConnected = await hydiService.initialize();

      // Initialize OBD2 service
      const obd2Service = ZareoOBD2Service.getInstance();
      const obd2Initialized = await obd2Service.initialize();

      setAppState({
        isInitialized: true,
        obd2Connected: obd2Initialized,
        hydiConnected,
        bluetoothEnabled,
        privacyConsent,
        error: null,
      });

      // Show initialization status
      const connectedServices = [];
      const failedServices = [];

      if (hydiConnected) connectedServices.push('Hydi AI');
      else failedServices.push('Hydi AI');

      if (bluetoothEnabled) connectedServices.push('Bluetooth');
      else failedServices.push('Bluetooth');

      if (obd2Initialized) connectedServices.push('OBD2 System');
      else failedServices.push('OBD2 System');

      if (connectedServices.length > 0) {
        Toast.show({
          type: 'success',
          text1: 'Z-AREO Initialized',
          text2: `Connected: ${connectedServices.join(', ')}`,
          visibilityTime: 4000,
        });
      }

      if (failedServices.length > 0) {
        Toast.show({
          type: 'info',
          text1: 'Some Services Unavailable',
          text2: `Check: ${failedServices.join(', ')}`,
          visibilityTime: 6000,
        });
      }

    } catch (error) {
      console.error('App initialization error:', error);
      setAppState(prev => ({
        ...prev,
        isInitialized: true,
        error: error instanceof Error ? error.message : 'Unknown error',
      }));

      Alert.alert(
        'Z-AREO Initialization Error',
        `Failed to initialize the app: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease check your device settings and try again.`,
        [
          {text: 'Retry', onPress: initializeApp},
          {
            text: 'Continue with Limited Features',
            onPress: () => setAppState(prev => ({...prev, isInitialized: true})),
          },
        ]
      );
    }
  };

  const theme = isDarkMode ? zareoDarkTheme : zareoLightTheme;

  if (!appState.isInitialized) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#2196F3" />
        <LoadingScreen />
      </SafeAreaView>
    );
  }

  return (
    <GestureHandlerRootView style={{flex: 1}}>
      <PaperProvider theme={theme}>
        <ZareoProvider>
          <OBD2Provider>
            <SafeAreaView style={styles.container}>
              <StatusBar
                barStyle={isDarkMode ? 'light-content' : 'dark-content'}
                backgroundColor={theme.colors.primary}
              />
              <NavigationContainer theme={theme}>
                <DrawerNavigator />
              </NavigationContainer>
              <Toast />
            </SafeAreaView>
          </OBD2Provider>
        </ZareoProvider>
      </PaperProvider>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    padding: 20,
  },
  loadingTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2196F3',
    marginTop: 20,
    marginBottom: 8,
  },
  loadingSubtitle: {
    fontSize: 16,
    color: '#757575',
    textAlign: 'center',
    marginBottom: 40,
  },
});

export default App;