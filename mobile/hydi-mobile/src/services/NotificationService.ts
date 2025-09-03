import PushNotification from 'react-native-push-notification';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

interface NotificationConfig {
  title: string;
  message: string;
  playSound?: boolean;
  soundName?: string;
  vibrate?: boolean;
  vibration?: number;
  priority?: 'high' | 'low' | 'default';
  category?: string;
  userInfo?: any;
  actions?: string[];
}

interface ScheduledNotification extends NotificationConfig {
  id: string;
  date: Date;
}

class NotificationServiceClass {
  private isInitialized = false;
  private notificationQueue: NotificationConfig[] = [];
  private scheduledNotifications: ScheduledNotification[] = [];

  async initialize(): Promise<void> {
    if (this.isInitialized) {
      console.log('NotificationService already initialized');
      return;
    }

    try {
      // Configure push notifications
      PushNotification.configure({
        onRegister: (token) => {
          console.log('Push notification token:', token);
          this.savePushToken(token.token);
        },

        onNotification: (notification) => {
          console.log('Notification received:', notification);
          this.handleNotificationReceived(notification);
        },

        onAction: (notification) => {
          console.log('Notification action:', notification);
          this.handleNotificationAction(notification);
        },

        onRegistrationError: (err) => {
          console.error('Push notification registration error:', err);
        },

        permissions: {
          alert: true,
          badge: true,
          sound: true,
        },

        popInitialNotification: true,
        requestPermissions: Platform.OS === 'ios',
      });

      // Create default notification channel for Android
      if (Platform.OS === 'android') {
        PushNotification.createChannel(
          {
            channelId: 'hydi-default',
            channelName: 'Hydi Notifications',
            channelDescription: 'Default notification channel for Hydi mobile app',
            playSound: true,
            soundName: 'default',
            importance: 4, // High importance
            vibrate: true,
          },
          (created) => console.log(`Notification channel created: ${created}`)
        );

        // Create channel for system alerts
        PushNotification.createChannel(
          {
            channelId: 'hydi-system',
            channelName: 'System Alerts',
            channelDescription: 'Important system notifications and alerts',
            playSound: true,
            soundName: 'default',
            importance: 4,
            vibrate: true,
          },
          (created) => console.log(`System channel created: ${created}`)
        );

        // Create channel for module updates
        PushNotification.createChannel(
          {
            channelId: 'hydi-modules',
            channelName: 'Module Updates',
            channelDescription: 'Notifications about module status changes',
            playSound: false,
            importance: 2, // Low importance
            vibrate: false,
          },
          (created) => console.log(`Modules channel created: ${created}`)
        );
      }

      this.isInitialized = true;
      console.log('NotificationService initialized successfully');

      // Process any queued notifications
      await this.processNotificationQueue();

    } catch (error) {
      console.error('NotificationService initialization failed:', error);
      throw error;
    }
  }

  private async savePushToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem('push_notification_token', token);
      console.log('Push token saved');
    } catch (error) {
      console.error('Failed to save push token:', error);
    }
  }

  async getPushToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('push_notification_token');
    } catch (error) {
      console.error('Failed to get push token:', error);
      return null;
    }
  }

  private handleNotificationReceived(notification: any): void {
    console.log('Processing received notification:', notification);
    
    // Handle different types of notifications
    switch (notification.userInfo?.type) {
      case 'system_alert':
        this.handleSystemAlert(notification);
        break;
      case 'module_update':
        this.handleModuleUpdate(notification);
        break;
      case 'repl_response':
        this.handleReplResponse(notification);
        break;
      default:
        console.log('Unknown notification type');
    }
  }

  private handleNotificationAction(notification: any): void {
    console.log('Processing notification action:', notification);
    
    // Handle notification actions based on the action identifier
    switch (notification.action) {
      case 'OPEN_REPL':
        // Navigate to REPL screen
        break;
      case 'OPEN_MODULES':
        // Navigate to modules screen
        break;
      case 'DISMISS':
        // Just dismiss the notification
        break;
      default:
        console.log('Unknown notification action');
    }
  }

  private handleSystemAlert(notification: any): void {
    // Handle system-level alerts
    console.log('System alert received:', notification.userInfo);
  }

  private handleModuleUpdate(notification: any): void {
    // Handle module status updates
    console.log('Module update received:', notification.userInfo);
  }

  private handleReplResponse(notification: any): void {
    // Handle REPL command responses
    console.log('REPL response received:', notification.userInfo);
  }

  async showLocalNotification(config: NotificationConfig): Promise<void> {
    if (!this.isInitialized) {
      console.log('NotificationService not initialized, queuing notification');
      this.notificationQueue.push(config);
      return;
    }

    try {
      const notification = {
        ...config,
        channelId: this.getChannelId(config.category),
        id: Date.now().toString(),
        date: new Date(),
        allowWhileIdle: true,
        ignoreInForeground: false,
      };

      PushNotification.localNotification(notification);
      console.log('Local notification sent:', notification.title);
    } catch (error) {
      console.error('Failed to show local notification:', error);
    }
  }

  async scheduleNotification(config: NotificationConfig, date: Date): Promise<string> {
    if (!this.isInitialized) {
      throw new Error('NotificationService not initialized');
    }

    const id = Date.now().toString();
    const scheduledNotification: ScheduledNotification = {
      ...config,
      id,
      date,
    };

    try {
      const notification = {
        ...config,
        channelId: this.getChannelId(config.category),
        id,
        date,
        allowWhileIdle: true,
      };

      PushNotification.localNotificationSchedule(notification);
      
      this.scheduledNotifications.push(scheduledNotification);
      await this.saveScheduledNotifications();
      
      console.log('Notification scheduled:', scheduledNotification.title, 'for', date);
      return id;
    } catch (error) {
      console.error('Failed to schedule notification:', error);
      throw error;
    }
  }

  async cancelNotification(id: string): Promise<void> {
    try {
      PushNotification.cancelLocalNotifications({ id });
      
      this.scheduledNotifications = this.scheduledNotifications.filter(
        notification => notification.id !== id
      );
      await this.saveScheduledNotifications();
      
      console.log('Notification canceled:', id);
    } catch (error) {
      console.error('Failed to cancel notification:', error);
    }
  }

  async cancelAllNotifications(): Promise<void> {
    try {
      PushNotification.cancelAllLocalNotifications();
      this.scheduledNotifications = [];
      await this.saveScheduledNotifications();
      console.log('All notifications canceled');
    } catch (error) {
      console.error('Failed to cancel all notifications:', error);
    }
  }

  private getChannelId(category?: string): string {
    switch (category) {
      case 'system':
        return 'hydi-system';
      case 'modules':
        return 'hydi-modules';
      default:
        return 'hydi-default';
    }
  }

  private async processNotificationQueue(): Promise<void> {
    if (this.notificationQueue.length === 0) {
      return;
    }

    console.log(`Processing ${this.notificationQueue.length} queued notifications`);
    
    for (const notification of this.notificationQueue) {
      await this.showLocalNotification(notification);
    }
    
    this.notificationQueue = [];
  }

  private async saveScheduledNotifications(): Promise<void> {
    try {
      await AsyncStorage.setItem(
        'scheduled_notifications',
        JSON.stringify(this.scheduledNotifications)
      );
    } catch (error) {
      console.error('Failed to save scheduled notifications:', error);
    }
  }

  private async loadScheduledNotifications(): Promise<void> {
    try {
      const saved = await AsyncStorage.getItem('scheduled_notifications');
      if (saved) {
        this.scheduledNotifications = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load scheduled notifications:', error);
    }
  }

  // Predefined notification types for Hydi
  async notifySystemConnected(): Promise<void> {
    await this.showLocalNotification({
      title: '🧠 Hydi Connected',
      message: 'Successfully connected to Hydi system',
      category: 'system',
      vibrate: true,
      vibration: 300,
    });
  }

  async notifySystemDisconnected(): Promise<void> {
    await this.showLocalNotification({
      title: '⚠️ Hydi Disconnected',
      message: 'Lost connection to Hydi system',
      category: 'system',
      vibrate: true,
      vibration: 500,
      priority: 'high',
    });
  }

  async notifyModuleStatusChange(moduleName: string, status: string): Promise<void> {
    await this.showLocalNotification({
      title: `Module ${status}`,
      message: `${moduleName} is now ${status}`,
      category: 'modules',
      vibrate: false,
    });
  }

  async notifyVoiceCommandProcessed(command: string): Promise<void> {
    await this.showLocalNotification({
      title: '🎤 Voice Command',
      message: `Processed: "${command}"`,
      category: 'default',
      vibrate: true,
      vibration: 200,
    });
  }

  async notifyREPLError(error: string): Promise<void> {
    await this.showLocalNotification({
      title: '❌ REPL Error',
      message: error,
      category: 'system',
      vibrate: true,
      vibration: 400,
      priority: 'high',
    });
  }

  async notifyExperimentActivated(experimentName: string): Promise<void> {
    await this.showLocalNotification({
      title: '🧪 Experiment Active',
      message: `${experimentName} experiment is now running`,
      category: 'modules',
      vibrate: true,
      vibration: 300,
      priority: 'high',
    });
  }

  // Check notification permissions
  async checkPermissions(): Promise<any> {
    return new Promise((resolve) => {
      PushNotification.checkPermissions(resolve);
    });
  }

  async requestPermissions(): Promise<any> {
    return new Promise((resolve) => {
      PushNotification.requestPermissions().then(resolve);
    });
  }

  cleanup(): void {
    console.log('NotificationService cleanup');
    this.isInitialized = false;
    this.notificationQueue = [];
  }

  getScheduledNotifications(): ScheduledNotification[] {
    return [...this.scheduledNotifications];
  }

  async clearBadge(): Promise<void> {
    if (Platform.OS === 'ios') {
      PushNotification.setApplicationIconBadgeNumber(0);
    }
  }

  async setBadgeCount(count: number): Promise<void> {
    if (Platform.OS === 'ios') {
      PushNotification.setApplicationIconBadgeNumber(count);
    }
  }
}

export const NotificationService = new NotificationServiceClass();