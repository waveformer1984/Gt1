import { MD3DarkTheme } from 'react-native-paper';

export const hydiTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    // Primary colors - Neural network inspired
    primary: '#00E5FF', // Cyan for primary actions
    onPrimary: '#000000',
    primaryContainer: '#1A1A2E', // Dark blue-purple
    onPrimaryContainer: '#00E5FF',
    
    // Secondary colors - Purple accent
    secondary: '#BB86FC', // Light purple
    onSecondary: '#000000',
    secondaryContainer: '#3700B3', // Dark purple
    onSecondaryContainer: '#BB86FC',
    
    // Tertiary colors - Green for success states
    tertiary: '#03DAC6', // Teal
    onTertiary: '#000000',
    tertiaryContainer: '#004940',
    onTertiaryContainer: '#03DAC6',
    
    // Error colors - Red for warnings/errors
    error: '#CF6679',
    onError: '#000000',
    errorContainer: '#93000A',
    onErrorContainer: '#FFDAD6',
    
    // Background colors
    background: '#0F0F23', // Very dark blue
    onBackground: '#E6E6FA', // Light lavender
    surface: '#16213E', // Dark blue-gray
    onSurface: '#E6E6FA',
    surfaceVariant: '#1E2749', // Slightly lighter blue
    onSurfaceVariant: '#C4C6D0',
    
    // Outline and other colors
    outline: '#3949AB', // Blue outline
    outlineVariant: '#2E3A59',
    shadow: '#000000',
    scrim: '#000000',
    inverseSurface: '#E6E6FA',
    inverseOnSurface: '#0F0F23',
    inversePrimary: '#006B7A',
    
    // Additional custom colors for Hydi
    accent: '#FF6B35', // Orange accent for highlights
    neural: '#00E5FF', // Neural activity color
    warning: '#FFA726', // Warning orange
    success: '#4CAF50', // Success green
    info: '#2196F3', // Info blue
    disabled: '#555555',
    
    // Module status colors
    moduleActive: '#4CAF50',
    moduleInactive: '#757575',
    moduleError: '#F44336',
    moduleLoading: '#FF9800',
    
    // REPL colors
    replPrompt: '#00E5FF',
    replOutput: '#E6E6FA',
    replError: '#CF6679',
    replComment: '#BB86FC',
    
    // Voice interface colors
    voiceActive: '#4CAF50',
    voiceListening: '#FF9800',
    voiceProcessing: '#2196F3',
    voiceError: '#F44336',
  },
  
  // Typography
  fonts: {
    ...MD3DarkTheme.fonts,
    // Monospace for REPL
    mono: {
      fontFamily: 'monospace',
      fontWeight: '400' as const,
    },
    // Bold for headers
    displayLarge: {
      ...MD3DarkTheme.fonts.displayLarge,
      fontWeight: '700' as const,
    },
  },
  
  // Custom spacing
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  
  // Border radius
  borderRadius: {
    small: 4,
    medium: 8,
    large: 16,
    round: 50,
  },
  
  // Animation durations
  animation: {
    fast: 150,
    normal: 300,
    slow: 500,
  },
  
  // Shadows
  shadows: {
    small: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.3,
      shadowRadius: 2,
      elevation: 2,
    },
    medium: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 4,
    },
    large: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 8,
    },
  },
  
  // Component specific styles
  components: {
    card: {
      backgroundColor: '#16213E',
      borderColor: '#3949AB',
      borderWidth: 1,
    },
    button: {
      primary: {
        backgroundColor: '#00E5FF',
        color: '#000000',
      },
      secondary: {
        backgroundColor: 'transparent',
        borderColor: '#00E5FF',
        borderWidth: 1,
        color: '#00E5FF',
      },
    },
    input: {
      backgroundColor: '#1E2749',
      borderColor: '#3949AB',
      color: '#E6E6FA',
      placeholderColor: '#C4C6D0',
    },
  },
  
  // Status colors mapping
  statusColors: {
    active: '#4CAF50',
    inactive: '#757575',
    error: '#F44336',
    loading: '#FF9800',
    warning: '#FFA726',
    success: '#4CAF50',
    info: '#2196F3',
  },
};

export type HydiTheme = typeof hydiTheme;