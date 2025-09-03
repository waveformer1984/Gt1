import React, {useEffect, useState} from 'react';
import {
  SafeAreaView,
  StatusBar,
  StyleSheet,
  useColorScheme,
  Alert,
  PermissionsAndroid,
  Platform,
} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createDrawerNavigator} from '@react-navigation/drawer';
import {PaperProvider} from 'react-native-paper';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Toast from 'react-native-toast-message';

// Screens
import DashboardScreen from './src/screens/DashboardScreen';
import PluginsScreen from './src/screens/PluginsScreen';
import WebServicesScreen from './src/screens/WebServicesScreen';
import HydiREPLScreen from './src/screens/HydiREPLScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import DeviceManagementScreen from './src/screens/DeviceManagementScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';

// Services
import {HydiService} from './src/services/HydiService';
import {WebServicesClient} from './src/services/WebServicesClient';
import {NotificationService} from './src/services/NotificationService';

// Context
import {AppProvider} from './src/context/AppContext';
import {HydiProvider} from './src/context/HydiContext';

// Theme
import {lightTheme, darkTheme} from './src/theme/theme';

const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();

interface AppState {
  isInitialized: boolean;
  hydiConnected: boolean;
  webServicesConnected: boolean;
  error: string | null;
}

const TabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName = '';

          switch (route.name) {
            case 'Dashboard':
              iconName = 'dashboard';
              break;
            case 'Plugins':
              iconName = 'extension';
              break;
            case 'WebServices':
              iconName = 'cloud';
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
        tabBarActiveTintColor: '#6200EE',
        tabBarInactiveTintColor: '#757575',
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopWidth: 1,
          borderTopColor: '#E0E0E0',
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
      })}>
      <Tab.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={{title: 'Dashboard'}}
      />
      <Tab.Screen 
        name="Plugins" 
        component={PluginsScreen}
        options={{title: 'Plugins'}}
      />
      <Tab.Screen 
        name="WebServices" 
        component={WebServicesScreen}
        options={{title: 'Services'}}
      />
      <Tab.Screen 
        name="Hydi" 
        component={HydiREPLScreen}
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
          width: 280,
        },
        drawerActiveTintColor: '#6200EE',
        drawerInactiveTintColor: '#757575',
        headerStyle: {
          backgroundColor: '#6200EE',
        },
        headerTintColor: '#FFFFFF',
      }}>
      <Drawer.Screen 
        name="MainTabs" 
        component={TabNavigator}
        options={{
          title: 'ballsDeepnit Mobile',
          drawerIcon: ({color}) => <Icon name="home" size={24} color={color} />,
        }}
      />
      <Drawer.Screen 
        name="DeviceManagement" 
        component={DeviceManagementScreen}
        options={{
          title: 'Device Management',
          drawerIcon: ({color}) => <Icon name="devices" size={24} color={color} />,
        }}
      />
      <Drawer.Screen 
        name="Notifications" 
        component={NotificationsScreen}
        options={{
          title: 'Notifications',
          drawerIcon: ({color}) => <Icon name="notifications" size={24} color={color} />,
        }}
      />
    </Drawer.Navigator>
  );
};

const App: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const [appState, setAppState] = useState<AppState>({
    isInitialized: false,
    hydiConnected: false,
    webServicesConnected: false,
    error: null,
  });

  useEffect(() => {
    initializeApp();
  }, []);

  const requestPermissions = async () => {
    if (Platform.OS === 'android') {
      try {
        const permissions = [
          PermissionsAndroid.PERMISSIONS.CAMERA,
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          PermissionsAndroid.PERMISSIONS.BLUETOOTH,
          PermissionsAndroid.PERMISSIONS.BLUETOOTH_ADMIN,
        ];

        const granted = await PermissionsAndroid.requestMultiple(permissions);
        
        const allGranted = Object.values(granted).every(
          permission => permission === PermissionsAndroid.RESULTS.GRANTED
        );

        if (!allGranted) {
          Alert.alert(
            'Permissions Required',
            'Some features may not work without the required permissions.',
            [{text: 'OK', onPress: () => {}}]
          );
        }
      } catch (err) {
        console.warn('Permission request error:', err);
      }
    }
  };

  const initializeApp = async () => {
    try {
      setAppState(prev => ({...prev, error: null}));

      // Request permissions
      await requestPermissions();

      // Initialize notification service
      await NotificationService.initialize();

      // Initialize Hydi service
      const hydiService = HydiService.getInstance();
      const hydiConnected = await hydiService.initialize();

      // Initialize web services client
      const webServicesClient = WebServicesClient.getInstance();
      const webServicesConnected = await webServicesClient.initialize();

      setAppState({
        isInitialized: true,
        hydiConnected,
        webServicesConnected,
        error: null,
      });

      // Show connection status
      if (hydiConnected && webServicesConnected) {
        Toast.show({
          type: 'success',
          text1: 'Connected',
          text2: 'Hydi and Web Services connected successfully',
        });
      } else {
        const failedServices = [];
        if (!hydiConnected) failedServices.push('Hydi');
        if (!webServicesConnected) failedServices.push('Web Services');
        
        Toast.show({
          type: 'error',
          text1: 'Connection Issues',
          text2: `Failed to connect to: ${failedServices.join(', ')}`,
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
        'Initialization Error',
        'Failed to initialize the app. Please check your connection and try again.',
        [
          {text: 'Retry', onPress: initializeApp},
          {text: 'Continue', onPress: () => {}},
        ]
      );
    }
  };

  const theme = isDarkMode ? darkTheme : lightTheme;

  return (
    <GestureHandlerRootView style={{flex: 1}}>
      <PaperProvider theme={theme}>
        <AppProvider>
          <HydiProvider>
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
          </HydiProvider>
        </AppProvider>
      </PaperProvider>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
});

export default App;