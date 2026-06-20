import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing, Typography } from '@/constants/theme';
import { useAuth } from '@/hooks/use-auth';

export default function ProfileScreen() {
  const { user, signOut } = useAuth();

  return (
    <ThemedView style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          <ThemedText style={Typography.h2}>Profile</ThemedText>
          <ThemedText style={Typography.body} themeColor="textSecondary">
            {user?.email}
          </ThemedText>
        </View>
        <Button
          title="Sign Out"
          variant="outline"
          onPress={signOut}
          style={styles.signOut}
        />
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    padding: Spacing.four,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.two,
  },
  signOut: {
    marginBottom: Spacing.four,
  },
});
