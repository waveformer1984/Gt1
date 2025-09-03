import React, { useEffect, useState } from 'react';
import {
  StatusBar,
  StyleSheet,
  View,
  Alert,
  AppState,
  AppStateStatus,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Provider as PaperProvider } from 'react-native-paper';

// Import screens
import HomeScreen from './src/screens/HomeScreen';
import REPLScreen from './src/screens/REPLScreen';
import ModulesScreen from './src/screens/ModulesScreen';
import VoiceScreen from './src/screens/VoiceScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import LoginScreen from './src/screens/LoginScreen';
import SystemStatusScreen from './src/screens/SystemStatusScreen';
import ExperimentsScreen from './src/screens/ExperimentsScreen';

// Import services
import { HydiService } from './src/services/HydiService';
import { NotificationService } from './src/services/NotificationService';
import { AuthService } from './src/services/AuthService';

// Import context
import { HydiProvider } from './src/context/HydiContext';
import { ThemeProvider } from './src/context/ThemeContext';

// Import theme
import { hydiTheme } from './src/theme/HydiTheme';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Tab Navigator Component
function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Home':
              iconName = focused ? 'home' : 'home';
              break;
            case 'REPL':
              iconName = focused ? 'terminal' : 'terminal';
              break;
            case 'Modules':
              iconName = focused ? 'extension' : 'extension';
              break;
            case 'Voice':
              iconName = focused ? 'mic' : 'mic-none';
              break;
            case 'Settings':
              iconName = focused ? 'settings' : 'settings';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: hydiTheme.colors.primary,
        tabBarInactiveTintColor: hydiTheme.colors.disabled,
        tabBarStyle: {
          backgroundColor: hydiTheme.colors.surface,
          borderTopColor: hydiTheme.colors.outline,
        },
        headerStyle: {
          backgroundColor: hydiTheme.colors.primaryContainer,
        },
        headerTintColor: hydiTheme.colors.onPrimaryContainer,
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{ title: 'Hydi Control' }}
      />
      <Tab.Screen 
        name="REPL" 
        component={REPLScreen}
        options={{ title: 'AI REPL' }}
      />
      <Tab.Screen 
        name="Modules" 
        component={ModulesScreen}
        options={{ title: 'Modules' }}
      />
      <Tab.Screen 
        name="Voice" 
        component={VoiceScreen}
        options={{ title: 'Voice Control' }}
      />
      <Tab.Screen 
        name="Settings" 
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
    </Tab.Navigator>
  );
}

// Main App Component
function App(): JSX.Element {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [appState, setAppState] = useState<AppStateStatus>(AppState.currentState);

  useEffect(() => {
    initializeApp();
    setupAppStateListener();
    
    return () => {
      cleanup();
    };
  }, []);

  const initializeApp = async () => {
    try {
      // Initialize services
      await NotificationService.initialize();
      await HydiService.initialize();
      
      // Check authentication status
      const authStatus = await AuthService.checkAuthStatus();
      setIsAuthenticated(authStatus);
      
      // Load user preferences
      await loadUserPreferences();
      
    } catch (error) {
      console.error('App initialization error:', error);
      Alert.alert(
        'Initialization Error',
        'Failed to initialize Hydi mobile app. Please restart the application.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const setupAppStateListener = () => {
    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  };

  const handleAppStateChange = (nextAppState: AppStateStatus) => {
    if (appState.match(/inactive|background/) && nextAppState === 'active') {
      // App has come to the foreground
      HydiService.reconnect();
    } else if (nextAppState.match(/inactive|background/)) {
      // App is going to background
      HydiService.handleBackground();
    }
    
    setAppState(nextAppState);
  };

  const loadUserPreferences = async () => {
    try {
      const preferences = await AsyncStorage.getItem('user_preferences');
      if (preferences) {
        const parsedPreferences = JSON.parse(preferences);
        // Apply user preferences
        await HydiService.applyUserPreferences(parsedPreferences);
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
  };

  const cleanup = () => {
    HydiService.cleanup();
    NotificationService.cleanup();
  };

  if (isLoading) {
    // You could replace this with a custom loading screen
    return (
      <View style={styles.loadingContainer}>
        <Icon name="psychology" size={64} color={hydiTheme.colors.primary} />
      </View>
    );
  }

  return (
    <PaperProvider theme={hydiTheme}>
      <ThemeProvider>
        <HydiProvider>
          <NavigationContainer theme={hydiTheme}>
            <StatusBar
              barStyle="light-content"
              backgroundColor={hydiTheme.colors.primaryContainer}
            />
            <Stack.Navigator
              screenOptions={{
                headerShown: false,
              }}
            >
              {!isAuthenticated ? (
                <Stack.Screen name="Login" component={LoginScreen} />
              ) : (
                <>
                  <Stack.Screen name="Main" component={TabNavigator} />
                  <Stack.Screen 
                    name="SystemStatus" 
                    component={SystemStatusScreen}
                    options={{
                      headerShown: true,
                      title: 'System Status',
                      headerStyle: {
                        backgroundColor: hydiTheme.colors.primaryContainer,
                      },
                      headerTintColor: hydiTheme.colors.onPrimaryContainer,
                    }}
                  />
                  <Stack.Screen 
                    name="Experiments" 
                    component={ExperimentsScreen}
                    options={{
                      headerShown: true,
                      title: 'Experimental Modules',
                      headerStyle: {
                        backgroundColor: hydiTheme.colors.errorContainer,
                      },
                      headerTintColor: hydiTheme.colors.onErrorContainer,
                    }}
                  />
                </>
              )}
            </Stack.Navigator>
          </NavigationContainer>
        </HydiProvider>
      </ThemeProvider>
    </PaperProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
});

export default App;