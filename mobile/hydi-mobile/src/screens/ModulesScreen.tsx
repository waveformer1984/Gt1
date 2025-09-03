import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Animated,
  Alert,
} from 'react-native';
import {
  Text,
  Card,
  Switch,
  Chip,
  Button,
  Surface,
  ProgressBar,
  IconButton,
  Searchbar,
  useTheme,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';

import { useHydi, useHydiModules } from '../context/HydiContext';
import { HydiModule } from '../services/HydiService';
import { hydiTheme } from '../theme/HydiTheme';

interface ModuleCardProps {
  module: HydiModule;
  onToggle: (moduleId: string, enabled: boolean) => void;
  animationDelay: number;
}

const ModuleCard: React.FC<ModuleCardProps> = ({ module, onToggle, animationDelay }) => {
  const theme = useTheme();
  const [fadeAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      delay: animationDelay,
      useNativeDriver: true,
    }).start();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.colors.success;
      case 'inactive':
        return theme.colors.onSurfaceVariant;
      case 'error':
        return theme.colors.error;
      case 'loading':
        return theme.colors.warning;
      default:
        return theme.colors.onSurfaceVariant;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return 'check-circle';
      case 'inactive':
        return 'radio-button-unchecked';
      case 'error':
        return 'error';
      case 'loading':
        return 'hourglass-empty';
      default:
        return 'help';
    }
  };

  const getTypeColor = (type: string) => {
    return type === 'core' ? theme.colors.primary : theme.colors.accent;
  };

  const handleToggle = () => {
    if (module.status === 'loading') {
      return; // Don't allow toggle while loading
    }

    if (module.type === 'experimental' && !module.enabled) {
      Alert.alert(
        'Experimental Module',
        `${module.name} is an experimental module. Enabling it may cause unexpected behavior. Continue?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Enable', onPress: () => onToggle(module.id, true) },
        ]
      );
    } else {
      onToggle(module.id, !module.enabled);
    }
  };

  return (
    <Animated.View style={[styles.moduleCard, { opacity: fadeAnim }]}>
      <Card mode="elevated" style={styles.card}>
        <Card.Content>
          <View style={styles.moduleHeader}>
            <View style={styles.moduleInfo}>
              <View style={styles.moduleTitleRow}>
                <Text variant="titleMedium" style={styles.moduleTitle}>
                  {module.name}
                </Text>
                <Chip
                  mode="outlined"
                  compact
                  style={[
                    styles.typeChip,
                    { borderColor: getTypeColor(module.type) },
                  ]}
                  textStyle={{ color: getTypeColor(module.type), fontSize: 10 }}
                >
                  {module.type.toUpperCase()}
                </Chip>
              </View>
              
              <Text variant="bodySmall" style={styles.moduleDescription}>
                {module.description}
              </Text>
              
              <View style={styles.statusRow}>
                <Icon
                  name={getStatusIcon(module.status)}
                  size={16}
                  color={getStatusColor(module.status)}
                />
                <Text
                  variant="bodySmall"
                  style={[styles.statusText, { color: getStatusColor(module.status) }]}
                >
                  {module.status.charAt(0).toUpperCase() + module.status.slice(1)}
                </Text>
                
                <Text variant="bodySmall" style={styles.lastUpdated}>
                  Updated: {new Date(module.lastUpdated).toLocaleTimeString()}
                </Text>
              </View>
            </View>
            
            <View style={styles.moduleControls}>
              <Switch
                value={module.enabled}
                onValueChange={handleToggle}
                disabled={module.status === 'loading'}
                thumbColor={module.enabled ? theme.colors.primary : theme.colors.outline}
                trackColor={{
                  false: theme.colors.surfaceVariant,
                  true: `${theme.colors.primary}40`,
                }}
              />
            </View>
          </View>
          
          {module.status === 'loading' && (
            <ProgressBar
              indeterminate
              color={theme.colors.primary}
              style={styles.loadingBar}
            />
          )}
          
          {module.logs && module.logs.length > 0 && (
            <View style={styles.logsSection}>
              <Text variant="bodySmall" style={styles.logsTitle}>
                Recent Logs:
              </Text>
              {module.logs.slice(0, 3).map((log, index) => (
                <Text
                  key={index}
                  variant="bodySmall"
                  style={styles.logEntry}
                  numberOfLines={1}
                >
                  • {log}
                </Text>
              ))}
            </View>
          )}
        </Card.Content>
      </Card>
    </Animated.View>
  );
};

const ModulesScreen: React.FC = ({ navigation }: any) => {
  const theme = useTheme();
  const { isConnected, isRefreshing, refreshData } = useHydi();
  const { modules, toggleModule, coreModules, experimentalModules } = useHydiModules();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'core' | 'experimental'>('all');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive' | 'error'>('all');

  const filteredModules = modules.filter(module => {
    const matchesSearch = module.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         module.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || module.type === filterType;
    const matchesStatus = filterStatus === 'all' || module.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  const handleToggleModule = async (moduleId: string, enabled: boolean) => {
    try {
      await toggleModule(moduleId, enabled);
    } catch (error) {
      Alert.alert(
        'Module Toggle Failed',
        error instanceof Error ? error.message : 'Unknown error occurred',
        [{ text: 'OK' }]
      );
    }
  };

  const navigateToExperiments = () => {
    navigation.navigate('Experiments');
  };

  const getActiveCount = () => {
    return modules.filter(m => m.enabled && m.status === 'active').length;
  };

  const getErrorCount = () => {
    return modules.filter(m => m.status === 'error').length;
  };

  const renderHeader = () => (
    <Surface style={styles.header}>
      <View style={styles.headerContent}>
        <Text variant="titleLarge" style={styles.headerTitle}>
          🔧 Modules
        </Text>
        
        <View style={styles.headerStats}>
          <Chip
            icon="extension"
            style={[styles.statChip, { backgroundColor: `${theme.colors.primary}20` }]}
            textStyle={{ color: theme.colors.primary }}
          >
            {getActiveCount()} Active
          </Chip>
          
          {getErrorCount() > 0 && (
            <Chip
              icon="error"
              style={[styles.statChip, { backgroundColor: `${theme.colors.error}20` }]}
              textStyle={{ color: theme.colors.error }}
            >
              {getErrorCount()} Error
            </Chip>
          )}
        </View>
      </View>
      
      <Searchbar
        placeholder="Search modules..."
        onChangeText={setSearchQuery}
        value={searchQuery}
        style={styles.searchBar}
        iconColor={theme.colors.primary}
      />
      
      <View style={styles.filtersRow}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.filterChips}>
            <Chip
              mode={filterType === 'all' ? 'flat' : 'outlined'}
              onPress={() => setFilterType('all')}
              style={styles.filterChip}
              selected={filterType === 'all'}
            >
              All ({modules.length})
            </Chip>
            <Chip
              mode={filterType === 'core' ? 'flat' : 'outlined'}
              onPress={() => setFilterType('core')}
              style={styles.filterChip}
              selected={filterType === 'core'}
            >
              Core ({coreModules.length})
            </Chip>
            <Chip
              mode={filterType === 'experimental' ? 'flat' : 'outlined'}
              onPress={() => setFilterType('experimental')}
              style={styles.filterChip}
              selected={filterType === 'experimental'}
            >
              Experimental ({experimentalModules.length})
            </Chip>
          </View>
        </ScrollView>
        
        <IconButton
          icon="tune"
          onPress={() => {
            // Open advanced filters modal
          }}
        />
      </View>
    </Surface>
  );

  const renderQuickActions = () => (
    <View style={styles.quickActions}>
      <Button
        mode="outlined"
        icon="science"
        onPress={navigateToExperiments}
        style={styles.actionButton}
      >
        Experiments
      </Button>
      
      <Button
        mode="outlined"
        icon="refresh"
        onPress={refreshData}
        loading={isRefreshing}
        disabled={!isConnected}
        style={styles.actionButton}
      >
        Refresh
      </Button>
    </View>
  );

  return (
    <LinearGradient
      colors={[theme.colors.background, theme.colors.surfaceVariant]}
      style={styles.container}
    >
      {renderHeader()}
      
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={refreshData}
            colors={[theme.colors.primary]}
            progressBackgroundColor={theme.colors.surface}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {renderQuickActions()}
        
        {!isConnected && (
          <Card mode="elevated" style={styles.warningCard}>
            <Card.Content>
              <View style={styles.warningContent}>
                <Icon name="wifi-off" size={24} color={theme.colors.error} />
                <Text variant="bodyMedium" style={styles.warningText}>
                  Not connected to Hydi system. Module controls are disabled.
                </Text>
              </View>
            </Card.Content>
          </Card>
        )}
        
        <View style={styles.modulesContainer}>
          {filteredModules.length === 0 ? (
            <Card mode="elevated" style={styles.emptyCard}>
              <Card.Content style={styles.emptyContent}>
                <Icon name="search-off" size={48} color={theme.colors.onSurfaceVariant} />
                <Text variant="titleMedium" style={styles.emptyTitle}>
                  No modules found
                </Text>
                <Text variant="bodyMedium" style={styles.emptyDescription}>
                  Try adjusting your search or filter criteria
                </Text>
              </Card.Content>
            </Card>
          ) : (
            filteredModules.map((module, index) => (
              <ModuleCard
                key={module.id}
                module={module}
                onToggle={handleToggleModule}
                animationDelay={index * 100}
              />
            ))
          )}
        </View>
        
        <View style={styles.bottomSpacing} />
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    backgroundColor: hydiTheme.colors.surface,
    paddingBottom: hydiTheme.spacing.md,
    elevation: 4,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: hydiTheme.spacing.md,
  },
  headerTitle: {
    color: hydiTheme.colors.primary,
    fontWeight: 'bold',
  },
  headerStats: {
    flexDirection: 'row',
    gap: hydiTheme.spacing.sm,
  },
  statChip: {
    borderWidth: 1,
  },
  searchBar: {
    marginHorizontal: hydiTheme.spacing.md,
    marginBottom: hydiTheme.spacing.sm,
    backgroundColor: hydiTheme.colors.surfaceVariant,
  },
  filtersRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: hydiTheme.spacing.md,
  },
  filterChips: {
    flexDirection: 'row',
    gap: hydiTheme.spacing.sm,
    paddingRight: hydiTheme.spacing.md,
  },
  filterChip: {
    marginRight: hydiTheme.spacing.xs,
  },
  scrollView: {
    flex: 1,
  },
  quickActions: {
    flexDirection: 'row',
    padding: hydiTheme.spacing.md,
    gap: hydiTheme.spacing.md,
  },
  actionButton: {
    flex: 1,
  },
  warningCard: {
    marginHorizontal: hydiTheme.spacing.md,
    marginBottom: hydiTheme.spacing.md,
    backgroundColor: `${hydiTheme.colors.error}10`,
    borderColor: hydiTheme.colors.error,
    borderWidth: 1,
  },
  warningContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: hydiTheme.spacing.md,
  },
  warningText: {
    color: hydiTheme.colors.error,
    flex: 1,
  },
  modulesContainer: {
    padding: hydiTheme.spacing.md,
  },
  moduleCard: {
    marginBottom: hydiTheme.spacing.md,
  },
  card: {
    backgroundColor: hydiTheme.colors.surface,
    borderColor: hydiTheme.colors.outline,
    borderWidth: 1,
  },
  moduleHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  moduleInfo: {
    flex: 1,
    marginRight: hydiTheme.spacing.md,
  },
  moduleTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: hydiTheme.spacing.xs,
  },
  moduleTitle: {
    color: hydiTheme.colors.onSurface,
    fontWeight: 'bold',
    flex: 1,
  },
  typeChip: {
    marginLeft: hydiTheme.spacing.sm,
  },
  moduleDescription: {
    color: hydiTheme.colors.onSurfaceVariant,
    marginBottom: hydiTheme.spacing.sm,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: hydiTheme.spacing.xs,
  },
  statusText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  lastUpdated: {
    fontSize: 12,
    color: hydiTheme.colors.onSurfaceVariant,
    marginLeft: 'auto',
  },
  moduleControls: {
    alignItems: 'center',
  },
  loadingBar: {
    marginTop: hydiTheme.spacing.sm,
    height: 4,
    borderRadius: 2,
  },
  logsSection: {
    marginTop: hydiTheme.spacing.md,
    padding: hydiTheme.spacing.sm,
    backgroundColor: hydiTheme.colors.surfaceVariant,
    borderRadius: hydiTheme.borderRadius.small,
  },
  logsTitle: {
    color: hydiTheme.colors.onSurfaceVariant,
    fontWeight: 'bold',
    marginBottom: hydiTheme.spacing.xs,
  },
  logEntry: {
    color: hydiTheme.colors.onSurfaceVariant,
    fontFamily: 'monospace',
    fontSize: 11,
    marginVertical: 1,
  },
  emptyCard: {
    backgroundColor: hydiTheme.colors.surface,
    borderColor: hydiTheme.colors.outline,
    borderWidth: 1,
  },
  emptyContent: {
    alignItems: 'center',
    padding: hydiTheme.spacing.xxl,
  },
  emptyTitle: {
    color: hydiTheme.colors.onSurfaceVariant,
    marginTop: hydiTheme.spacing.md,
    marginBottom: hydiTheme.spacing.sm,
  },
  emptyDescription: {
    color: hydiTheme.colors.onSurfaceVariant,
    textAlign: 'center',
  },
  bottomSpacing: {
    height: hydiTheme.spacing.xxl,
  },
});

export default ModulesScreen;