import { useEffect, useState } from 'react';
import { ActivityIndicator, Linking, ScrollView, StyleSheet, View } from 'react-native';
import { Image } from 'expo-image';
import { Stack, useLocalSearchParams } from 'expo-router';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { DecisionBadge } from '@/components/ui/badge';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BorderRadius, Colors, FlatBorder, Spacing, Typography } from '@/constants/theme';
import { getItem } from '@/services/items';
import { formatDate } from '@/utils/format';
import type { Item } from '@/types/item';

export default function ItemDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [item, setItem] = useState<Item | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getItem(id)
      .then(setItem)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <ThemedView style={styles.center}>
        <ActivityIndicator size="large" color={Colors.light.primary} />
      </ThemedView>
    );
  }

  if (!item) {
    return (
      <ThemedView style={styles.center}>
        <ThemedText style={Typography.body} themeColor="textSecondary">
          Item not found.
        </ThemedText>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <Stack.Screen
        options={{
          title: item.itemName,
          headerStyle: { backgroundColor: Colors.light.background },
          headerTintColor: Colors.light.text,
          headerShadowVisible: false,
        }}
      />
      <ScrollView contentContainerStyle={styles.scroll}>
        {item.photoUrl ? (
          <Image source={{ uri: item.photoUrl }} style={styles.photo} contentFit="cover" />
        ) : null}

        <View style={styles.headerRow}>
          <ThemedText style={Typography.h1} numberOfLines={2}>
            {item.itemName}
          </ThemedText>
          <DecisionBadge decision={item.decision} size="md" />
        </View>

        <ThemedText style={Typography.caption} themeColor="textSecondary">
          {item.category} · {item.condition} · {formatDate(item.createdAt)}
        </ThemedText>

        {item.description ? (
          <ThemedText style={[Typography.body, styles.desc]}>{item.description}</ThemedText>
        ) : null}

        {item.selectedService ? (
          <Card variant="outlined" style={styles.serviceCard}>
            <ThemedText style={Typography.small} themeColor="textSecondary">
              SERVICE
            </ThemedText>
            <ThemedText style={Typography.h3}>{item.selectedService.name}</ThemedText>
            {item.selectedService.scheduledDate ? (
              <ThemedText style={Typography.caption} themeColor="textSecondary">
                {item.selectedService.scheduledDate}
              </ThemedText>
            ) : null}
            {item.selectedService.url ? (
              <Button
                title="Open service"
                variant="outline"
                size="sm"
                style={styles.serviceBtn}
                onPress={() => Linking.openURL(item.selectedService!.url)}
              />
            ) : null}
          </Card>
        ) : null}
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.light.background,
  },
  scroll: {
    padding: Spacing.four,
    gap: Spacing.two,
  },
  photo: {
    width: '100%',
    height: 280,
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.two,
    ...FlatBorder,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.two,
  },
  desc: {
    marginTop: Spacing.one,
  },
  serviceCard: {
    marginTop: Spacing.three,
    gap: Spacing.one,
  },
  serviceBtn: {
    marginTop: Spacing.two,
    alignSelf: 'flex-start',
  },
});
