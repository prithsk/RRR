import { View, StyleSheet, type ViewProps, type ViewStyle } from 'react-native';

import { BorderRadius, FlatBorder, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

interface CardProps extends ViewProps {
  variant?: 'outlined' | 'filled' | 'plain';
  padding?: keyof typeof Spacing;
  style?: ViewStyle;
}

export function Card({
  variant = 'outlined',
  padding = 'four',
  style,
  children,
  ...rest
}: CardProps) {
  const theme = useTheme();

  return (
    <View
      style={[
        styles.base,
        { padding: Spacing[padding] },
        variant === 'outlined' && {
          backgroundColor: theme.backgroundElement,
          ...FlatBorder,
        },
        variant === 'filled' && {
          backgroundColor: theme.backgroundElement,
        },
        variant === 'plain' && {
          backgroundColor: 'transparent',
        },
        style,
      ]}
      {...rest}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: BorderRadius.lg,
  },
});
