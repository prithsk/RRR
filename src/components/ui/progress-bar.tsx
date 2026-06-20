import { View, StyleSheet } from 'react-native';
import Animated, {
  useAnimatedStyle,
  withTiming,
  Easing,
} from 'react-native-reanimated';

import { BorderRadius } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

interface ProgressBarProps {
  progress: number; // 0–1
  height?: number;
}

export function ProgressBar({ progress, height = 6 }: ProgressBarProps) {
  const theme = useTheme();

  const fillStyle = useAnimatedStyle(() => ({
    width: withTiming(`${Math.round(Math.min(1, Math.max(0, progress)) * 100)}%`, {
      duration: 400,
      easing: Easing.out(Easing.cubic),
    }),
  }));

  return (
    <View style={[styles.track, { height, backgroundColor: theme.backgroundElement }]}>
      <Animated.View
        style={[styles.fill, { height, backgroundColor: theme.primary }, fillStyle]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    width: '100%',
    borderRadius: BorderRadius.full,
    overflow: 'hidden',
  },
  fill: {
    borderRadius: BorderRadius.full,
  },
});
