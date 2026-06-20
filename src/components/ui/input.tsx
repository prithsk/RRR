import { useState } from 'react';
import { TextInput, View, StyleSheet, type TextInputProps, type ViewStyle } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { BorderRadius, Fonts, Typography } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  containerStyle?: ViewStyle;
}

export function Input({ label, error, containerStyle, style, ...rest }: InputProps) {
  const theme = useTheme();
  const [focused, setFocused] = useState(false);

  const borderColor = error ? theme.error : theme.border;

  return (
    <View style={containerStyle}>
      {label && <ThemedText style={[Typography.captionBold, styles.label]}>{label}</ThemedText>}
      <TextInput
        style={[
          styles.input,
          {
            backgroundColor: focused ? theme.backgroundElement : theme.background,
            color: theme.text,
            borderColor,
            fontFamily: Fonts.body,
          },
          style,
        ]}
        placeholderTextColor={theme.textSecondary}
        onFocus={(e) => {
          setFocused(true);
          rest.onFocus?.(e);
        }}
        onBlur={(e) => {
          setFocused(false);
          rest.onBlur?.(e);
        }}
        {...rest}
      />
      {error && <ThemedText style={[Typography.small, { color: theme.error }]}>{error}</ThemedText>}
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    marginBottom: 6,
  },
  input: {
    fontSize: 16,
    lineHeight: 22,
    borderWidth: 2,
    borderRadius: BorderRadius.md,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
});
