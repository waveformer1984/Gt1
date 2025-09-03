import AsyncStorage from '@react-native-async-storage/async-storage';
import Keychain from 'react-native-keychain';
import DeviceInfo from 'react-native-device-info';

interface AuthCredentials {
  username: string;
  password: string;
  serverUrl: string;
}

interface AuthSession {
  token: string;
  refreshToken: string;
  expiresAt: number;
  user: UserProfile;
}

interface UserProfile {
  id: string;
  username: string;
  email: string;
  permissions: string[];
  preferences: any;
}

interface BiometricConfig {
  enabled: boolean;
  type: 'touchId' | 'faceId' | 'fingerprint' | null;
}

class AuthServiceClass {
  private currentSession: AuthSession | null = null;
  private biometricConfig: BiometricConfig = { enabled: false, type: null };
  
  private readonly KEYCHAIN_SERVICE = 'hydi_mobile_auth';
  private readonly STORAGE_KEY_SESSION = 'auth_session';
  private readonly STORAGE_KEY_BIOMETRIC = 'biometric_config';

  async initialize(): Promise<void> {
    try {
      // Load saved session
      await this.loadSession();
      
      // Initialize biometric authentication
      await this.initializeBiometrics();
      
      console.log('AuthService initialized successfully');
    } catch (error) {
      console.error('AuthService initialization failed:', error);
    }
  }

  private async loadSession(): Promise<void> {
    try {
      const sessionData = await AsyncStorage.getItem(this.STORAGE_KEY_SESSION);
      if (sessionData) {
        const session = JSON.parse(sessionData);
        
        // Check if session is still valid
        if (session.expiresAt > Date.now()) {
          this.currentSession = session;
          console.log('Loaded valid session for user:', session.user.username);
        } else {
          console.log('Session expired, clearing stored session');
          await this.clearSession();
        }
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  }

  private async initializeBiometrics(): Promise<void> {
    try {
      // Load biometric configuration
      const biometricData = await AsyncStorage.getItem(this.STORAGE_KEY_BIOMETRIC);
      if (biometricData) {
        this.biometricConfig = JSON.parse(biometricData);
      }

      // Check if biometrics are supported
      const biometryType = await TouchID.isSupported();
      if (biometryType) {
        this.biometricConfig.type = biometryType as any;
        console.log('Biometric authentication supported:', biometryType);
      } else {
        this.biometricConfig.type = null;
        console.log('Biometric authentication not supported');
      }
    } catch (error) {
      console.error('Failed to initialize biometrics:', error);
      this.biometricConfig = { enabled: false, type: null };
    }
  }

  async login(credentials: AuthCredentials): Promise<boolean> {
    try {
      const deviceId = await DeviceInfo.getUniqueId();
      const deviceInfo = {
        id: deviceId,
        model: await DeviceInfo.getModel(),
        platform: await DeviceInfo.getSystemName(),
        version: await DeviceInfo.getSystemVersion(),
        appVersion: await DeviceInfo.getVersion(),
      };

      // Make login request to Hydi backend
      const response = await fetch(`${credentials.serverUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: credentials.username,
          password: credentials.password,
          deviceInfo,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Login failed');
      }

      const authData = await response.json();
      
      // Create session
      const session: AuthSession = {
        token: authData.token,
        refreshToken: authData.refreshToken,
        expiresAt: Date.now() + (authData.expiresIn * 1000),
        user: authData.user,
      };

      // Save session
      await this.saveSession(session);
      this.currentSession = session;

      // Save credentials to keychain if biometric is enabled
      if (this.biometricConfig.enabled) {
        await this.saveCredentialsToKeychain(credentials);
      }

      console.log('Login successful for user:', session.user.username);
      return true;

    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async loginWithBiometrics(): Promise<boolean> {
    if (!this.biometricConfig.enabled || !this.biometricConfig.type) {
      throw new Error('Biometric authentication not enabled or supported');
    }

    try {
      // Authenticate with biometrics
      await TouchID.authenticate('Authenticate to access Hydi', {
        title: 'Hydi Authentication',
        subtitle: 'Use your biometric to sign in',
        fallbackLabel: 'Use passcode',
        cancelLabel: 'Cancel',
      });

      // Retrieve credentials from keychain
      const credentials = await Keychain.getCredentials(this.KEYCHAIN_SERVICE);
      if (!credentials || credentials.username === false) {
        throw new Error('No saved credentials found');
      }

      const authCredentials: AuthCredentials = JSON.parse(credentials.password);
      
      // Perform login
      return await this.login(authCredentials);

    } catch (error) {
      console.error('Biometric login failed:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      // Notify server about logout if we have a valid session
      if (this.currentSession) {
        try {
          await fetch(`${this.getServerUrl()}/api/auth/logout`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${this.currentSession.token}`,
              'Content-Type': 'application/json',
            },
          });
        } catch (error) {
          console.warn('Failed to notify server about logout:', error);
        }
      }

      // Clear local session
      await this.clearSession();
      
      console.log('Logout successful');
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }

  async refreshToken(): Promise<boolean> {
    if (!this.currentSession?.refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${this.getServerUrl()}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.currentSession.refreshToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const authData = await response.json();
      
      // Update session
      this.currentSession.token = authData.token;
      this.currentSession.expiresAt = Date.now() + (authData.expiresIn * 1000);
      
      if (authData.refreshToken) {
        this.currentSession.refreshToken = authData.refreshToken;
      }

      await this.saveSession(this.currentSession);
      
      console.log('Token refreshed successfully');
      return true;

    } catch (error) {
      console.error('Token refresh failed:', error);
      await this.clearSession();
      return false;
    }
  }

  async enableBiometrics(credentials: AuthCredentials): Promise<void> {
    if (!this.biometricConfig.type) {
      throw new Error('Biometric authentication not supported on this device');
    }

    try {
      // Test biometric authentication
      await TouchID.authenticate('Enable biometric authentication for Hydi', {
        title: 'Enable Biometric Login',
        subtitle: 'Authenticate to enable biometric login',
        fallbackLabel: 'Cancel',
        cancelLabel: 'Cancel',
      });

      // Save credentials to keychain
      await this.saveCredentialsToKeychain(credentials);
      
      // Update biometric configuration
      this.biometricConfig.enabled = true;
      await this.saveBiometricConfig();

      console.log('Biometric authentication enabled');
    } catch (error) {
      console.error('Failed to enable biometric authentication:', error);
      throw error;
    }
  }

  async disableBiometrics(): Promise<void> {
    try {
      // Remove credentials from keychain
      await Keychain.resetCredentials(this.KEYCHAIN_SERVICE);
      
      // Update biometric configuration
      this.biometricConfig.enabled = false;
      await this.saveBiometricConfig();

      console.log('Biometric authentication disabled');
    } catch (error) {
      console.error('Failed to disable biometric authentication:', error);
      throw error;
    }
  }

  private async saveSession(session: AuthSession): Promise<void> {
    try {
      await AsyncStorage.setItem(this.STORAGE_KEY_SESSION, JSON.stringify(session));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  }

  private async clearSession(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.STORAGE_KEY_SESSION);
      this.currentSession = null;
    } catch (error) {
      console.error('Failed to clear session:', error);
    }
  }

  private async saveCredentialsToKeychain(credentials: AuthCredentials): Promise<void> {
    try {
      await Keychain.setCredentials(
        credentials.username,
        JSON.stringify(credentials),
        this.KEYCHAIN_SERVICE
      );
    } catch (error) {
      console.error('Failed to save credentials to keychain:', error);
      throw error;
    }
  }

  private async saveBiometricConfig(): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEY_BIOMETRIC,
        JSON.stringify(this.biometricConfig)
      );
    } catch (error) {
      console.error('Failed to save biometric configuration:', error);
    }
  }

  private getServerUrl(): string {
    // Get server URL from current session or default
    return this.currentSession?.user?.preferences?.serverUrl || 'http://localhost:8000';
  }

  // Public API methods
  async checkAuthStatus(): Promise<boolean> {
    if (!this.currentSession) {
      return false;
    }

    // Check if token is expired
    if (this.currentSession.expiresAt <= Date.now()) {
      console.log('Token expired, attempting refresh...');
      return await this.refreshToken();
    }

    return true;
  }

  getCurrentUser(): UserProfile | null {
    return this.currentSession?.user || null;
  }

  getAuthToken(): string | null {
    return this.currentSession?.token || null;
  }

  getBiometricConfig(): BiometricConfig {
    return { ...this.biometricConfig };
  }

  isLoggedIn(): boolean {
    return !!this.currentSession && this.currentSession.expiresAt > Date.now();
  }

  isBiometricSupported(): boolean {
    return !!this.biometricConfig.type;
  }

  isBiometricEnabled(): boolean {
    return this.biometricConfig.enabled && !!this.biometricConfig.type;
  }

  hasPermission(permission: string): boolean {
    return this.currentSession?.user?.permissions?.includes(permission) || false;
  }

  async updateUserPreferences(preferences: any): Promise<void> {
    if (!this.currentSession) {
      throw new Error('Not authenticated');
    }

    try {
      const response = await fetch(`${this.getServerUrl()}/api/user/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.currentSession.token}`,
        },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error('Failed to update preferences');
      }

      // Update local session
      this.currentSession.user.preferences = {
        ...this.currentSession.user.preferences,
        ...preferences,
      };

      await this.saveSession(this.currentSession);
      
      console.log('User preferences updated');
    } catch (error) {
      console.error('Failed to update user preferences:', error);
      throw error;
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    if (!this.currentSession) {
      throw new Error('Not authenticated');
    }

    try {
      const response = await fetch(`${this.getServerUrl()}/api/user/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.currentSession.token}`,
        },
        body: JSON.stringify({
          currentPassword,
          newPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to change password');
      }

      console.log('Password changed successfully');
    } catch (error) {
      console.error('Failed to change password:', error);
      throw error;
    }
  }

  cleanup(): void {
    this.currentSession = null;
    console.log('AuthService cleanup completed');
  }
}

export const AuthService = new AuthServiceClass();