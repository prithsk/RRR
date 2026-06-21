import { StyleSheet, View } from 'react-native';

import { Card } from '@/components/ui/card';
import { ThemedText } from '@/components/themed-text';
import { Colors, Spacing, Typography } from '@/constants/theme';

interface StatsCardProps {
  total: number;
  donate: number;
  sell: number;
  discard: number;
}

export function StatsCard({ total, donate, sell, discard }: StatsCardProps) {
  return (
    <Card variant="outlined" style={styles.card}>
      <ThemedText style={Typography.small} themeColor="textSecondary">
        ITEMS ANALYZED
      </ThemedText>
      <ThemedText style={styles.total}>{total}</ThemedText>
      <View style={styles.row}>
        <Stat label="Donated" value={donate} color={Colors.light.donate} />
        <Stat label="Sold" value={sell} color={Colors.light.sell} />
        <Stat label="Tossed" value={discard} color={Colors.light.discard} />
      </View>
    </Card>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={styles.stat}>
      <ThemedText style={[Typography.h3, { color }]}>{value}</ThemedText>
      <ThemedText style={Typography.small} themeColor="textSecondary">
        {label}
      </ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Spacing.one,
  },
  total: {
    fontFamily: Typography.display.fontFamily,
    fontSize: 48,
    lineHeight: 52,
    color: Colors.light.text,
  },
  row: {
    flexDirection: 'row',
    gap: Spacing.four,
    marginTop: Spacing.two,
  },
  stat: {
    alignItems: 'center',
    gap: 2,
  },
});
