import {
  Pressable,
  StyleSheet,
  ActivityIndicator,
  View,
  type PressableProps,
  type ViewStyle,
  type TextStyle,
} from 'react-native';
import { useState } from 'react';

import { ThemedText } from '@/components/themed-text';
import { BorderRadius, FlatBorder, Typography } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<PressableProps, 'style'> {
  title: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  style?: ViewStyle;
}

export function Button({
  title,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  icon,
  style,
  ...rest
}: ButtonProps) {
  const theme = useTheme();
  const [pressed, setPressed] = useState(false);

  const variantStyles: Record<
    ButtonVariant,
    { bg: string; pressedBg: string; text: string; border: string }
  > = {
    primary: {
      bg: theme.primary,
      pressedBg: theme.accent,
      text: '#FBF3E4',
      border: theme.border,
    },
    secondary: {
      bg: theme.backgroundElement,
      pressedBg: theme.backgroundSelected,
      text: theme.text,
      border: theme.border,
    },
    outline: {
      bg: 'transparent',
      pressedBg: theme.primaryLight,
      text: theme.text,
      border: theme.border,
    },
    ghost: {
      bg: 'transparent',
      pressedBg: theme.primaryLight,
      text: theme.primary,
      border: 'transparent',
    },
    danger: {
      bg: theme.error,
      pressedBg: '#8E2A21',
      text: '#FBF3E4',
      border: theme.border,
    },
  };

  const sizeStyles: Record<ButtonSize, { container: ViewStyle; text: TextStyle }> = {
    sm: { container: { paddingVertical: 8, paddingHorizontal: 16 }, text: Typography.buttonSmall },
    md: { container: { paddingVertical: 14, paddingHorizontal: 24 }, text: Typography.button },
    lg: { container: { paddingVertical: 18, paddingHorizontal: 32 }, text: Typography.button },
  };

  const v = variantStyles[variant];
  const s = sizeStyles[size];
  const isDisabled = disabled || loading;

  return (
    <Pressable
      onPressIn={() => setPressed(true)}
      onPressOut={() => setPressed(false)}
      disabled={isDisabled}
      style={[
        styles.base,
        s.container,
        {
          backgroundColor: isDisabled
            ? theme.backgroundSelected
            : pressed
              ? v.pressedBg
              : v.bg,
          borderColor: variant === 'ghost' ? 'transparent' : theme.border,
          borderWidth: variant === 'ghost' ? 0 : FlatBorder.borderWidth,
          transform: [{ translateY: pressed && !isDisabled ? 1 : 0 }],
        },
        style,
      ]}
      {...rest}
    >
      {loading ? (
        <ActivityIndicator size="small" color={v.text} />
      ) : (
        <View style={styles.content}>
          {icon}
          <ThemedText style={[s.text, { color: isDisabled ? theme.textSecondary : v.text }]}>
            {title}
          </ThemedText>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: BorderRadius.md,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
});
