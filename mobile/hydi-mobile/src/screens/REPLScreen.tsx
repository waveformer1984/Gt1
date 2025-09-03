import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Animated,
  Vibration,
} from 'react-native';
import {
  Text,
  Button,
  IconButton,
  Surface,
  Card,
  Chip,
  Menu,
  useTheme,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';

import { HydiService, REPLResponse } from '../services/HydiService';
import { useHydi } from '../context/HydiContext';
import { hydiTheme } from '../theme/HydiTheme';

interface REPLEntry {
  id: string;
  type: 'command' | 'output' | 'error' | 'system';
  content: string;
  timestamp: Date;
  executionTime?: number;
}

const REPLScreen: React.FC = () => {
  const theme = useTheme();
  const { isConnected } = useHydi();
  const [entries, setEntries] = useState<REPLEntry[]>([]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [menuVisible, setMenuVisible] = useState(false);
  
  const scrollViewRef = useRef<ScrollView>(null);
  const inputRef = useRef<TextInput>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  // Common Hydi commands for auto-completion
  const commonCommands = [
    'help',
    'status',
    'modules list',
    'modules enable',
    'modules disable',
    'voice start',
    'voice stop',
    'repl clear',
    'repl history',
    'system info',
    'experiments list',
    'experiments toggle',
    'context save',
    'context load',
    'shell exec',
    'tts speak',
    'memory dump',
    'logs show',
    'config get',
    'config set',
  ];

  useEffect(() => {
    // Add welcome message
    addSystemMessage(SYSTEM_MESSAGES.WELCOME);
    addSystemMessage(SYSTEM_MESSAGES.HELP_PROMPT);
    
    // Animate entrance
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 600,
      useNativeDriver: true,
    }).start();

    // Set up REPL response listener
    const unsubscribe = HydiService.onREPLResponse(handleREPLResponse);
    
    return () => {
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new entries are added
    if (scrollViewRef.current) {
      scrollViewRef.current.scrollToEnd({ animated: true });
    }
  }, [entries]);

  useEffect(() => {
    // Update suggestions based on current command
    if (currentCommand.length > 0) {
      const matchingSuggestions = commonCommands.filter(cmd =>
        cmd.toLowerCase().startsWith(currentCommand.toLowerCase())
      );
      setSuggestions(matchingSuggestions.slice(0, 5));
      setShowSuggestions(matchingSuggestions.length > 0);
    } else {
      setShowSuggestions(false);
    }
  }, [currentCommand]);

  const addSystemMessage = (message: string) => {
    const entry: REPLEntry = {
      id: Date.now().toString(),
      type: 'system',
      content: message,
      timestamp: new Date(),
    };
    setEntries(prev => [...prev, entry]);
  };

  const addCommandEntry = (command: string) => {
    const entry: REPLEntry = {
      id: Date.now().toString(),
      type: 'command',
      content: command,
      timestamp: new Date(),
    };
    setEntries(prev => [...prev, entry]);
  };

  const handleREPLResponse = (response: REPLResponse) => {
    const entry: REPLEntry = {
      id: (Date.now() + 1).toString(),
      type: response.success ? 'output' : 'error',
      content: response.output || response.error || 'No output',
      timestamp: new Date(response.timestamp),
      executionTime: response.executionTime,
    };
    setEntries(prev => [...prev, entry]);
    setIsExecuting(false);
    
    if (!response.success) {
      Vibration.vibrate(100);
    }
  };

  const executeCommand = async () => {
    if (!currentCommand.trim() || !isConnected) return;

    const command = currentCommand.trim();
    
    // Add command to history
    if (command !== commandHistory[commandHistory.length - 1]) {
      setCommandHistory(prev => [...prev, command]);
    }
    setHistoryIndex(-1);
    
    // Add command entry
    addCommandEntry(`> ${command}`);
    
    // Clear input and hide suggestions
    setCurrentCommand('');
    setShowSuggestions(false);
    setIsExecuting(true);
    
    try {
      // Handle local commands first
      if (handleLocalCommands(command)) {
        setIsExecuting(false);
        return;
      }
      
      // Execute command via HydiService
      await HydiService.executeREPLCommand(command);
    } catch (error) {
      const errorEntry: REPLEntry = {
        id: (Date.now() + 2).toString(),
        type: 'error',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setEntries(prev => [...prev, errorEntry]);
      setIsExecuting(false);
      Vibration.vibrate(100);
    }
  };

  const handleLocalCommands = (command: string): boolean => {
    const cmd = command.toLowerCase();
    
    switch (cmd) {
      case 'clear':
      case 'repl clear':
        setEntries([]);
        addSystemMessage('REPL cleared');
        return true;
        
      case 'history':
      case 'repl history':
        commandHistory.forEach((histCmd, index) => {
          const entry: REPLEntry = {
            id: `history-${index}`,
            type: 'output',
            content: `${index + 1}: ${histCmd}`,
            timestamp: new Date(),
          };
          setEntries(prev => [...prev, entry]);
        });
        return true;
        
      case 'help':
        const helpText = `
Available commands:
• help - Show this help
• clear - Clear REPL
• history - Show command history
• status - System status
• modules list - List all modules
• voice start/stop - Voice control
• experiments list - List experiments
        `.trim();
        const helpEntry: REPLEntry = {
          id: 'help-' + Date.now(),
          type: 'output',
          content: helpText,
          timestamp: new Date(),
        };
        setEntries(prev => [...prev, helpEntry]);
        return true;
        
      default:
        return false;
    }
  };

  const navigateHistory = (direction: 'up' | 'down') => {
    if (commandHistory.length === 0) return;
    
    let newIndex = historyIndex;
    
    if (direction === 'up') {
      newIndex = historyIndex + 1;
      if (newIndex >= commandHistory.length) {
        newIndex = commandHistory.length - 1;
      }
    } else {
      newIndex = historyIndex - 1;
      if (newIndex < -1) {
        newIndex = -1;
      }
    }
    
    setHistoryIndex(newIndex);
    
    if (newIndex === -1) {
      setCurrentCommand('');
    } else {
      setCurrentCommand(commandHistory[commandHistory.length - 1 - newIndex]);
    }
  };

  const insertSuggestion = (suggestion: string) => {
    setCurrentCommand(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const clearREPL = () => {
    setEntries([]);
    addSystemMessage('REPL cleared');
    setMenuVisible(false);
  };

  const exportREPL = () => {
    // Implementation for exporting REPL session
    addSystemMessage('Export functionality coming soon...');
    setMenuVisible(false);
  };

  const getEntryColor = (type: string) => {
    switch (type) {
      case 'command':
        return theme.colors.replPrompt;
      case 'output':
        return theme.colors.replOutput;
      case 'error':
        return theme.colors.replError;
      case 'system':
        return theme.colors.replComment;
      default:
        return theme.colors.onSurface;
    }
  };

  const getEntryIcon = (type: string) => {
    switch (type) {
      case 'command':
        return 'chevron-right';
      case 'output':
        return 'check';
      case 'error':
        return 'error';
      case 'system':
        return 'info';
      default:
        return 'circle';
    }
  };

  const renderEntry = (entry: REPLEntry) => (
    <View key={entry.id} style={styles.entryContainer}>
      <Icon
        name={getEntryIcon(entry.type)}
        size={16}
        color={getEntryColor(entry.type)}
        style={styles.entryIcon}
      />
      <View style={styles.entryContent}>
        <Text
          style={[
            styles.entryText,
            { color: getEntryColor(entry.type) },
            entry.type === 'command' && styles.commandText,
          ]}
        >
          {entry.content}
        </Text>
        <View style={styles.entryMeta}>
          <Text style={styles.entryTime}>
            {entry.timestamp.toLocaleTimeString()}
          </Text>
          {entry.executionTime && (
            <Text style={styles.executionTime}>
              {entry.executionTime}ms
            </Text>
          )}
        </View>
      </View>
    </View>
  );

  const renderSuggestions = () => (
    showSuggestions && (
      <Surface style={styles.suggestionsContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {suggestions.map((suggestion, index) => (
            <Chip
              key={index}
              mode="outlined"
              onPress={() => insertSuggestion(suggestion)}
              style={styles.suggestionChip}
              textStyle={styles.suggestionText}
            >
              {suggestion}
            </Chip>
          ))}
        </ScrollView>
      </Surface>
    )
  );

  return (
    <LinearGradient
      colors={[theme.colors.background, theme.colors.surfaceVariant]}
      style={styles.container}
    >
      <KeyboardAvoidingView
        style={styles.keyboardAvoidingView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <Surface style={styles.header}>
          <View style={styles.headerContent}>
            <Text variant="titleMedium" style={styles.headerTitle}>
              🧠 AI REPL
            </Text>
            <View style={styles.headerActions}>
              <Chip
                icon={() => (
                  <Icon
                    name="circle"
                    size={12}
                    color={isConnected ? theme.colors.success : theme.colors.error}
                  />
                )}
                style={[
                  styles.connectionChip,
                  {
                    backgroundColor: isConnected
                      ? `${theme.colors.success}20`
                      : `${theme.colors.error}20`,
                  },
                ]}
                textStyle={{
                  color: isConnected ? theme.colors.success : theme.colors.error,
                }}
              >
                {isConnected ? 'Connected' : 'Offline'}
              </Chip>
              <Menu
                visible={menuVisible}
                onDismiss={() => setMenuVisible(false)}
                anchor={
                  <IconButton
                    icon="more-vert"
                    onPress={() => setMenuVisible(true)}
                  />
                }
              >
                <Menu.Item onPress={clearREPL} title="Clear REPL" />
                <Menu.Item onPress={exportREPL} title="Export Session" />
              </Menu>
            </View>
          </View>
        </Surface>

        {/* REPL Output */}
        <Animated.View style={[styles.replContainer, { opacity: fadeAnim }]}>
          <ScrollView
            ref={scrollViewRef}
            style={styles.replOutput}
            showsVerticalScrollIndicator={false}
          >
            {entries.map(renderEntry)}
            {isExecuting && (
              <View style={styles.executingIndicator}>
                <Icon name="hourglass-empty" size={16} color={theme.colors.primary} />
                <Text style={styles.executingText}>Executing...</Text>
              </View>
            )}
          </ScrollView>
        </Animated.View>

        {/* Suggestions */}
        {renderSuggestions()}

        {/* Input */}
        <Surface style={styles.inputContainer}>
          <View style={styles.inputRow}>
            <IconButton
              icon="history"
              onPress={() => navigateHistory('up')}
              disabled={commandHistory.length === 0}
            />
            <TextInput
              ref={inputRef}
              style={styles.textInput}
              value={currentCommand}
              onChangeText={setCurrentCommand}
              placeholder="Enter Hydi command..."
              placeholderTextColor={theme.colors.onSurfaceVariant}
              multiline
              editable={isConnected && !isExecuting}
              onSubmitEditing={executeCommand}
              blurOnSubmit={false}
            />
            <IconButton
              icon="send"
              onPress={executeCommand}
              disabled={!isConnected || !currentCommand.trim() || isExecuting}
              iconColor={theme.colors.primary}
            />
          </View>
        </Surface>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  header: {
    elevation: 4,
    backgroundColor: hydiTheme.colors.surface,
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
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectionChip: {
    borderWidth: 1,
    marginRight: hydiTheme.spacing.sm,
  },
  replContainer: {
    flex: 1,
  },
  replOutput: {
    flex: 1,
    padding: hydiTheme.spacing.md,
  },
  entryContainer: {
    flexDirection: 'row',
    marginBottom: hydiTheme.spacing.sm,
    alignItems: 'flex-start',
  },
  entryIcon: {
    marginTop: 2,
    marginRight: hydiTheme.spacing.sm,
  },
  entryContent: {
    flex: 1,
  },
  entryText: {
    fontFamily: 'monospace',
    fontSize: 14,
    lineHeight: 20,
  },
  commandText: {
    fontWeight: 'bold',
  },
  entryMeta: {
    flexDirection: 'row',
    marginTop: hydiTheme.spacing.xs,
  },
  entryTime: {
    fontSize: 12,
    color: hydiTheme.colors.onSurfaceVariant,
    marginRight: hydiTheme.spacing.md,
  },
  executionTime: {
    fontSize: 12,
    color: hydiTheme.colors.primary,
  },
  executingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: hydiTheme.spacing.sm,
  },
  executingText: {
    marginLeft: hydiTheme.spacing.sm,
    color: hydiTheme.colors.primary,
    fontStyle: 'italic',
  },
  suggestionsContainer: {
    backgroundColor: hydiTheme.colors.surface,
    borderTopWidth: 1,
    borderTopColor: hydiTheme.colors.outline,
    paddingVertical: hydiTheme.spacing.sm,
  },
  suggestionChip: {
    marginHorizontal: hydiTheme.spacing.xs,
  },
  suggestionText: {
    fontSize: 12,
  },
  inputContainer: {
    backgroundColor: hydiTheme.colors.surface,
    borderTopWidth: 1,
    borderTopColor: hydiTheme.colors.outline,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: hydiTheme.spacing.sm,
  },
  textInput: {
    flex: 1,
    backgroundColor: hydiTheme.colors.surfaceVariant,
    borderRadius: hydiTheme.borderRadius.medium,
    paddingHorizontal: hydiTheme.spacing.md,
    paddingVertical: hydiTheme.spacing.sm,
    color: hydiTheme.colors.onSurface,
    fontFamily: 'monospace',
    fontSize: 16,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: hydiTheme.colors.outline,
  },
});

export default REPLScreen;