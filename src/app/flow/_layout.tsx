import { Stack } from 'expo-router';

import { useTheme } from '@/hooks/use-theme';

export default function FlowLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerStyle: { backgroundColor: theme.background },
        headerTintColor: theme.text,
        headerShadowVisible: false,
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="identify" options={{ title: 'Identifying...' }} />
      <Stack.Screen name="questions" options={{ title: 'Decision Time' }} />
      <Stack.Screen name="result" options={{ title: 'Result', headerBackVisible: false }} />
      <Stack.Screen name="services" options={{ title: 'Services' }} />
      <Stack.Screen name="confirm" options={{ title: 'Confirm', headerBackVisible: false }} />
    </Stack>
  );
}
