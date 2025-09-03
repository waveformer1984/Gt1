import React, { useEffect, useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Animated,
  Dimensions,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  Surface,
  ProgressBar,
  IconButton,
  Chip,
  useTheme,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';

import { HydiService, SystemStatus, HydiModule } from '../services/HydiService';
import { useHydi } from '../context/HydiContext';
import { hydiTheme } from '../theme/HydiTheme';

const { width } = Dimensions.get('window');

interface QuickAction {
  id: string;
  title: string;
  icon: string;
  action: () => void;
  color: string;
}

const HomeScreen: React.FC = ({ navigation }: any) => {
  const theme = useTheme();
  const { isConnected, systemStatus, modules } = useHydi();
  const [refreshing, setRefreshing] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(50));

  useEffect(() => {
    // Animate screen entrance
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await HydiService.getSystemStatus();
      await HydiService.getModules();
    } catch (error) {
      console.error('Refresh error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const quickActions: QuickAction[] = [
    {
      id: 'repl',
      title: 'AI REPL',
      icon: 'terminal',
      action: () => navigation.navigate('REPL'),
      color: theme.colors.primary,
    },
    {
      id: 'voice',
      title: 'Voice Control',
      icon: 'mic',
      action: () => navigation.navigate('Voice'),
      color: theme.colors.secondary,
    },
    {
      id: 'modules',
      title: 'Modules',
      icon: 'extension',
      action: () => navigation.navigate('Modules'),
      color: theme.colors.tertiary,
    },
    {
      id: 'status',
      title: 'System Status',
      icon: 'monitoring',
      action: () => navigation.navigate('SystemStatus'),
      color: theme.colors.accent,
    },
  ];

  const getConnectionStatusColor = () => {
    return isConnected ? theme.colors.success : theme.colors.error;
  };

  const getConnectionStatusText = () => {
    return isConnected ? 'Connected' : 'Disconnected';
  };

  const getActiveModulesCount = () => {
    return modules?.filter(module => module.enabled && module.status === 'active').length || 0;
  };

  const getTotalModulesCount = () => {
    return modules?.length || 0;
  };

  const renderQuickActions = () => (
    <View style={styles.quickActionsContainer}>
      <Text variant="titleMedium" style={styles.sectionTitle}>
        Quick Actions
      </Text>
      <View style={styles.quickActionsGrid}>
        {quickActions.map((action, index) => (
          <Animated.View
            key={action.id}
            style={[
              styles.quickActionItem,
              {
                opacity: fadeAnim,
                transform: [
                  {
                    translateY: slideAnim.interpolate({
                      inputRange: [0, 50],
                      outputRange: [0, 50 + index * 10],
                    }),
                  },
                ],
              },
            ]}
          >
            <Card
              mode="elevated"
              style={[styles.quickActionCard, { borderColor: action.color }]}
              onPress={action.action}
            >
              <Card.Content style={styles.quickActionContent}>
                <Icon name={action.icon} size={32} color={action.color} />
                <Text variant="bodyMedium" style={styles.quickActionText}>
                  {action.title}
                </Text>
              </Card.Content>
            </Card>
          </Animated.View>
        ))}
      </View>
    </View>
  );

  const renderSystemOverview = () => (
    <Animated.View
      style={[
        styles.overviewContainer,
        { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
      ]}
    >
      <Card mode="elevated" style={styles.overviewCard}>
        <Card.Content>
          <View style={styles.overviewHeader}>
            <Text variant="titleLarge" style={styles.overviewTitle}>
              🧠 Hydi System
            </Text>
            <Chip
              icon={() => (
                <Icon
                  name="circle"
                  size={12}
                  color={getConnectionStatusColor()}
                />
              )}
              style={[
                styles.statusChip,
                { backgroundColor: `${getConnectionStatusColor()}20` },
              ]}
              textStyle={{ color: getConnectionStatusColor() }}
            >
              {getConnectionStatusText()}
            </Chip>
          </View>
          
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text variant="headlineMedium" style={[styles.statValue, { color: theme.colors.primary }]}>
                {getActiveModulesCount()}
              </Text>
              <Text variant="bodySmall" style={styles.statLabel}>
                Active Modules
              </Text>
            </View>
            
            <View style={styles.statItem}>
              <Text variant="headlineMedium" style={[styles.statValue, { color: theme.colors.secondary }]}>
                {systemStatus?.uptime || '0m'}
              </Text>
              <Text variant="bodySmall" style={styles.statLabel}>
                Uptime
              </Text>
            </View>
            
            <View style={styles.statItem}>
              <Text variant="headlineMedium" style={[styles.statValue, { color: theme.colors.tertiary }]}>
                {systemStatus?.connections || 0}
              </Text>
              <Text variant="bodySmall" style={styles.statLabel}>
                Connections
              </Text>
            </View>
          </View>

          {systemStatus && (
            <View style={styles.metricsContainer}>
              <View style={styles.metricRow}>
                <Text variant="bodyMedium">CPU Usage</Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.primary }}>
                  {systemStatus.cpu.toFixed(1)}%
                </Text>
              </View>
              <ProgressBar
                progress={systemStatus.cpu / 100}
                color={theme.colors.primary}
                style={styles.progressBar}
              />
              
              <View style={styles.metricRow}>
                <Text variant="bodyMedium">Memory Usage</Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.secondary }}>
                  {systemStatus.memory.toFixed(1)}%
                </Text>
              </View>
              <ProgressBar
                progress={systemStatus.memory / 100}
                color={theme.colors.secondary}
                style={styles.progressBar}
              />
            </View>
          )}
        </Card.Content>
      </Card>
    </Animated.View>
  );

  const renderRecentActivity = () => (
    <Animated.View
      style={[
        styles.activityContainer,
        { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
      ]}
    >
      <Text variant="titleMedium" style={styles.sectionTitle}>
        Recent Activity
      </Text>
      <Card mode="elevated" style={styles.activityCard}>
        <Card.Content>
          <View style={styles.activityItem}>
            <Icon name="check-circle" size={20} color={theme.colors.success} />
            <View style={styles.activityText}>
              <Text variant="bodyMedium">REPL session started</Text>
              <Text variant="bodySmall" style={styles.activityTime}>
                2 minutes ago
              </Text>
            </View>
          </View>
          
          <View style={styles.activityItem}>
            <Icon name="extension" size={20} color={theme.colors.primary} />
            <View style={styles.activityText}>
              <Text variant="bodyMedium">Module 'context_memory' activated</Text>
              <Text variant="bodySmall" style={styles.activityTime}>
                5 minutes ago
              </Text>
            </View>
          </View>
          
          <View style={styles.activityItem}>
            <Icon name="mic" size={20} color={theme.colors.secondary} />
            <View style={styles.activityText}>
              <Text variant="bodyMedium">Voice command processed</Text>
              <Text variant="bodySmall" style={styles.activityTime}>
                8 minutes ago
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>
    </Animated.View>
  );

  return (
    <LinearGradient
      colors={[theme.colors.background, theme.colors.surfaceVariant]}
      style={styles.container}
    >
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[theme.colors.primary]}
            progressBackgroundColor={theme.colors.surface}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {renderSystemOverview()}
        {renderQuickActions()}
        {renderRecentActivity()}
        
        <View style={styles.bottomSpacing} />
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
    padding: hydiTheme.spacing.md,
  },
  overviewContainer: {
    marginBottom: hydiTheme.spacing.lg,
  },
  overviewCard: {
    backgroundColor: hydiTheme.colors.surface,
    borderColor: hydiTheme.colors.outline,
    borderWidth: 1,
  },
  overviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: hydiTheme.spacing.md,
  },
  overviewTitle: {
    color: hydiTheme.colors.primary,
    fontWeight: 'bold',
  },
  statusChip: {
    borderWidth: 1,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: hydiTheme.spacing.md,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontWeight: 'bold',
  },
  statLabel: {
    color: hydiTheme.colors.onSurfaceVariant,
    marginTop: hydiTheme.spacing.xs,
  },
  metricsContainer: {
    marginTop: hydiTheme.spacing.md,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: hydiTheme.spacing.xs,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    marginBottom: hydiTheme.spacing.md,
  },
  quickActionsContainer: {
    marginBottom: hydiTheme.spacing.lg,
  },
  sectionTitle: {
    color: hydiTheme.colors.onBackground,
    marginBottom: hydiTheme.spacing.md,
    fontWeight: 'bold',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionItem: {
    width: (width - hydiTheme.spacing.md * 3) / 2,
    marginBottom: hydiTheme.spacing.md,
  },
  quickActionCard: {
    backgroundColor: hydiTheme.colors.surface,
    borderWidth: 1,
    height: 100,
  },
  quickActionContent: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  quickActionText: {
    marginTop: hydiTheme.spacing.sm,
    textAlign: 'center',
    color: hydiTheme.colors.onSurface,
  },
  activityContainer: {
    marginBottom: hydiTheme.spacing.lg,
  },
  activityCard: {
    backgroundColor: hydiTheme.colors.surface,
    borderColor: hydiTheme.colors.outline,
    borderWidth: 1,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: hydiTheme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: hydiTheme.colors.outlineVariant,
  },
  activityText: {
    marginLeft: hydiTheme.spacing.md,
    flex: 1,
  },
  activityTime: {
    color: hydiTheme.colors.onSurfaceVariant,
    marginTop: hydiTheme.spacing.xs,
  },
  bottomSpacing: {
    height: hydiTheme.spacing.xxl,
  },
});

export default HomeScreen;