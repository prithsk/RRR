import { View, StyleSheet, type ViewStyle } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { BorderRadius, Typography } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import type { Decision } from '@/types/item';

interface BadgeProps {
  decision: Decision;
  size?: 'sm' | 'md' | 'lg';
  style?: ViewStyle;
}

export function DecisionBadge({ decision, size = 'md', style }: BadgeProps) {
  const theme = useTheme();

  const colorMap: Record<Decision, { bg: string; text: string }> = {
    DONATE: { bg: theme.donateBg, text: theme.donate },
    SELL: { bg: theme.sellBg, text: theme.sell },
    DISCARD: { bg: theme.discardBg, text: theme.discard },
  };

  const sizeMap = {
    sm: { paddingVertical: 2, paddingHorizontal: 8, ...Typography.small },
    md: { paddingVertical: 4, paddingHorizontal: 12, ...Typography.captionBold },
    lg: { paddingVertical: 8, paddingHorizontal: 20, ...Typography.button },
  };

  const c = colorMap[decision];
  const s = sizeMap[size];

  return (
    <View
      style={[
        styles.base,
        {
          backgroundColor: c.bg,
          paddingVertical: s.paddingVertical,
          paddingHorizontal: s.paddingHorizontal,
        },
        style,
      ]}
    >
      <ThemedText
        style={{
          color: c.text,
          fontFamily: s.fontFamily,
          fontSize: s.fontSize,
          lineHeight: s.lineHeight,
        }}
      >
        {decision}
      </ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: BorderRadius.full,
    alignSelf: 'flex-start',
  },
});
