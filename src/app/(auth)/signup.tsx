import { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ThemedText } from '@/components/themed-text';
import { BorderRadius, Colors, FlatBorder, Spacing, Typography } from '@/constants/theme';
import { useAuth } from '@/hooks/use-auth';

export default function SignupScreen() {
  const { signUp } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSignup() {
    if (!email.trim() || !password.trim() || !confirmPassword.trim()) {
      setError('Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await signUp(email.trim(), password);
    } catch (e: any) {
      setError(e.message ?? 'Signup failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <ThemedText style={styles.title}>Create Account</ThemedText>
            <ThemedText style={styles.subtitle}>
              Start making smarter decisions about your stuff.
            </ThemedText>
          </View>

          <View style={styles.form}>
            <Input
              label="EMAIL"
              placeholder="you@example.com"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              containerStyle={styles.inputContainer}
            />
            <Input
              label="PASSWORD"
              placeholder="At least 6 characters"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              containerStyle={styles.inputContainer}
            />
            <Input
              label="CONFIRM PASSWORD"
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry
              containerStyle={styles.inputContainer}
            />

            {error ? <ThemedText style={styles.error}>{error}</ThemedText> : null}

            <Button title="Create Account" onPress={handleSignup} loading={loading} size="lg" />

            <View style={styles.loginRow}>
              <ThemedText style={styles.loginText}>Already have an account?</ThemedText>
              <Pressable onPress={() => router.back()}>
                <ThemedText style={styles.loginLink}> Sign In</ThemedText>
              </Pressable>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: Spacing.five,
  },
  header: {
    alignItems: 'center',
    marginBottom: Spacing.five,
  },
  title: {
    ...Typography.h1,
    color: Colors.light.text,
    marginBottom: Spacing.two,
    textAlign: 'center',
  },
  subtitle: {
    ...Typography.body,
    color: Colors.light.textSecondary,
    textAlign: 'center',
  },
  form: {
    backgroundColor: Colors.light.backgroundElement,
    borderRadius: BorderRadius.xl,
    padding: Spacing.four,
    ...FlatBorder,
  },
  inputContainer: {
    marginBottom: Spacing.three,
  },
  error: {
    ...Typography.small,
    color: Colors.light.error,
    textAlign: 'center',
    marginBottom: Spacing.three,
  },
  loginRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: Spacing.four,
  },
  loginText: {
    ...Typography.caption,
    color: Colors.light.textSecondary,
  },
  loginLink: {
    ...Typography.captionBold,
    color: Colors.light.accent,
  },
});
