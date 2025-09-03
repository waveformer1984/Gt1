import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { HydiService, HydiModule, SystemStatus } from '../services/HydiService';

interface HydiContextType {
  // Connection state
  isConnected: boolean;
  connectionStatus: string;
  
  // System data
  systemStatus: SystemStatus | null;
  modules: HydiModule[];
  
  // Loading states
  isLoading: boolean;
  isRefreshing: boolean;
  
  // Error handling
  error: string | null;
  
  // Actions
  refreshData: () => Promise<void>;
  toggleModule: (moduleId: string, enabled: boolean) => Promise<void>;
  clearError: () => void;
  
  // Voice state
  isVoiceActive: boolean;
  voiceStatus: 'idle' | 'listening' | 'processing' | 'speaking';
  
  // REPL state
  replHistory: string[];
  
  // Notifications
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  autoClose?: boolean;
}

const HydiContext = createContext<HydiContextType | undefined>(undefined);

interface HydiProviderProps {
  children: ReactNode;
}

export const HydiProvider: React.FC<HydiProviderProps> = ({ children }) => {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // System data
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [modules, setModules] = useState<HydiModule[]>([]);
  
  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Error handling
  const [error, setError] = useState<string | null>(null);
  
  // Voice state
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState<'idle' | 'listening' | 'processing' | 'speaking'>('idle');
  
  // REPL state
  const [replHistory, setReplHistory] = useState<string[]>([]);
  
  // Notifications
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    initializeHydiContext();
    
    return () => {
      cleanup();
    };
  }, []);

  const initializeHydiContext = async () => {
    try {
      setIsLoading(true);
      
      // Set up event listeners
      setupEventListeners();
      
      // Initial data fetch
      await refreshData();
      
    } catch (err) {
      console.error('Failed to initialize Hydi context:', err);
      setError(err instanceof Error ? err.message : 'Initialization failed');
    } finally {
      setIsLoading(false);
    }
  };

  const setupEventListeners = () => {
    // Connection status listener
    const unsubscribeConnection = HydiService.onConnectionChange((connected) => {
      setIsConnected(connected);
      setConnectionStatus(HydiService.getConnectionStatus());
      
      if (connected) {
        addNotification({
          type: 'success',
          title: 'Connected',
          message: 'Successfully connected to Hydi system',
          autoClose: true,
        });
        // Refresh data when reconnected
        refreshData();
      } else {
        addNotification({
          type: 'warning',
          title: 'Disconnected',
          message: 'Lost connection to Hydi system',
          autoClose: true,
        });
      }
    });

    // System status updates
    const unsubscribeSystemStatus = HydiService.onSystemStatusUpdate((status) => {
      setSystemStatus(status);
    });

    // Module updates
    const unsubscribeModules = HydiService.onModuleUpdate((updatedModules) => {
      setModules(updatedModules);
    });

    // REPL responses
    const unsubscribeRepl = HydiService.onREPLResponse((response) => {
      // Update REPL history if needed
      console.log('REPL response received:', response);
    });

    // Store unsubscribe functions for cleanup using useRef
    unsubscribersRef.current = {
      unsubscribeConnection,
      unsubscribeSystemStatus,
      unsubscribeModules,
      unsubscribeRepl,
    };
  };

  const cleanup = () => {
    const unsubscribers = unsubscribersRef.current;
    if (unsubscribers) {
      Object.values(unsubscribers).forEach((unsubscribe: any) => {
        if (typeof unsubscribe === 'function') {
          unsubscribe();
        }
      });
    }
  };

  const refreshData = async () => {
    try {
      if (!isLoading) {
        setIsRefreshing(true);
      }
      
      setError(null);
      
      // Fetch system status and modules in parallel
      const [statusResult, modulesResult] = await Promise.allSettled([
        HydiService.getSystemStatus(),
        HydiService.getModules(),
      ]);

      if (statusResult.status === 'fulfilled') {
        setSystemStatus(statusResult.value);
      } else {
        console.error('Failed to fetch system status:', statusResult.reason);
      }

      if (modulesResult.status === 'fulfilled') {
        setModules(modulesResult.value);
      } else {
        console.error('Failed to fetch modules:', modulesResult.reason);
      }

      // Update connection status
      setIsConnected(HydiService.isConnected());
      setConnectionStatus(HydiService.getConnectionStatus());

    } catch (err) {
      console.error('Failed to refresh data:', err);
      setError(err instanceof Error ? err.message : 'Failed to refresh data');
      
      addNotification({
        type: 'error',
        title: 'Refresh Failed',
        message: 'Failed to refresh system data',
        autoClose: true,
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const toggleModule = async (moduleId: string, enabled: boolean) => {
    try {
      setError(null);
      
      await HydiService.toggleModule(moduleId, enabled);
      
      // Update the module in local state immediately for better UX
      setModules(prevModules =>
        prevModules.map(module =>
          module.id === moduleId
            ? { ...module, enabled, status: enabled ? 'loading' : 'inactive' }
            : module
        )
      );

      addNotification({
        type: 'success',
        title: 'Module Updated',
        message: `Module ${moduleId} ${enabled ? 'enabled' : 'disabled'}`,
        autoClose: true,
      });

      // Refresh modules to get updated status
      setTimeout(() => {
        HydiService.getModules().then(setModules);
      }, 1000);

    } catch (err) {
      console.error('Failed to toggle module:', err);
      setError(err instanceof Error ? err.message : 'Failed to toggle module');
      
      addNotification({
        type: 'error',
        title: 'Module Toggle Failed',
        message: `Failed to ${enabled ? 'enable' : 'disable'} module ${moduleId}`,
        autoClose: true,
      });
      
      // Revert the optimistic update
      await refreshData();
    }
  };

  const clearError = () => {
    setError(null);
  };

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };

    setNotifications(prev => [newNotification, ...prev]);

    // Auto-remove notification if autoClose is true
    if (notification.autoClose) {
      setTimeout(() => {
        removeNotification(newNotification.id);
      }, 5000); // Remove after 5 seconds
    }
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  // Derived state
  const getActiveModulesCount = () => {
    return modules.filter(module => module.enabled && module.status === 'active').length;
  };

  const getErrorModulesCount = () => {
    return modules.filter(module => module.status === 'error').length;
  };

  const getCoreModules = () => {
    return modules.filter(module => module.type === 'core');
  };

  const getExperimentalModules = () => {
    return modules.filter(module => module.type === 'experimental');
  };

  const contextValue: HydiContextType = {
    // Connection state
    isConnected,
    connectionStatus,
    
    // System data
    systemStatus,
    modules,
    
    // Loading states
    isLoading,
    isRefreshing,
    
    // Error handling
    error,
    clearError,
    
    // Actions
    refreshData,
    toggleModule,
    
    // Voice state
    isVoiceActive,
    voiceStatus,
    
    // REPL state
    replHistory,
    
    // Notifications
    notifications,
    addNotification,
    removeNotification,
  };

  return (
    <HydiContext.Provider value={contextValue}>
      {children}
    </HydiContext.Provider>
  );
};

export const useHydi = (): HydiContextType => {
  const context = useContext(HydiContext);
  if (context === undefined) {
    throw new Error('useHydi must be used within a HydiProvider');
  }
  return context;
};

// Additional hooks for specific data
export const useHydiModules = () => {
  const { modules, toggleModule } = useHydi();
  
  return {
    modules,
    toggleModule,
    coreModules: modules.filter(m => m.type === 'core'),
    experimentalModules: modules.filter(m => m.type === 'experimental'),
    activeModules: modules.filter(m => m.enabled && m.status === 'active'),
    errorModules: modules.filter(m => m.status === 'error'),
  };
};

export const useHydiConnection = () => {
  const { isConnected, connectionStatus, refreshData } = useHydi();
  
  return {
    isConnected,
    connectionStatus,
    reconnect: refreshData,
  };
};

export const useHydiNotifications = () => {
  const { notifications, addNotification, removeNotification } = useHydi();
  
  return {
    notifications,
    addNotification,
    removeNotification,
    latestNotification: notifications[0] || null,
    unreadCount: notifications.length,
  };
};