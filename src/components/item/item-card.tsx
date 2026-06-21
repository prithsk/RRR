import { Image } from 'expo-image';
import { Pressable, StyleSheet, View } from 'react-native';

import { DecisionBadge } from '@/components/ui/badge';
import { ThemedText } from '@/components/themed-text';
import { BorderRadius, Colors, FlatBorder, Spacing, Typography } from '@/constants/theme';
import { formatDate } from '@/utils/format';
import type { Item } from '@/types/item';

export function ItemCard({ item, onPress }: { item: Item; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        { backgroundColor: pressed ? Colors.light.backgroundSelected : Colors.light.backgroundElement },
      ]}
    >
      {item.photoUrl ? (
        <Image source={{ uri: item.photoUrl }} style={styles.thumb} contentFit="cover" />
      ) : (
        <View style={[styles.thumb, styles.thumbPlaceholder]}>
          <ThemedText style={styles.placeholderText}>{item.itemName.charAt(0).toUpperCase()}</ThemedText>
        </View>
      )}
      <View style={styles.body}>
        <ThemedText style={Typography.bodyBold} numberOfLines={1}>
          {item.itemName}
        </ThemedText>
        <ThemedText style={Typography.small} themeColor="textSecondary">
          {formatDate(item.createdAt)}
        </ThemedText>
        <DecisionBadge decision={item.decision} size="sm" style={styles.badge} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    gap: Spacing.three,
    padding: Spacing.two,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    ...FlatBorder,
  },
  thumb: {
    width: 64,
    height: 64,
    borderRadius: BorderRadius.sm,
    backgroundColor: Colors.light.primaryLight,
  },
  thumbPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontFamily: Typography.h2.fontFamily,
    fontSize: 24,
    color: Colors.light.accent,
  },
  body: {
    flex: 1,
    gap: 2,
  },
  badge: {
    marginTop: Spacing.half,
  },
});
