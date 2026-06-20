import { StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Typography } from '@/constants/theme';

export default function ServicesScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText style={Typography.h2}>Service Discovery</ThemedText>
      <ThemedText style={Typography.body} themeColor="textSecondary">
        Coming in Phase 4
      </ThemedText>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
});
