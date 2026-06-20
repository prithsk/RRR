import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { router } from 'expo-router';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ProgressBar } from '@/components/ui/progress-bar';
import { OptionButton } from '@/components/flow/option-button';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing, Typography } from '@/constants/theme';
import { useItemFlow } from '@/contexts/item-context';
import type { Urgency } from '@/types/item';

const TOTAL_STEPS = 4;

export default function QuestionsScreen() {
  const { identification, setAnswers } = useItemFlow();
  const itemName = identification?.itemName ?? 'this item';

  const [step, setStep] = useState(0);

  // Answers
  const [wantToDonate, setWantToDonate] = useState<boolean | null>(null);
  const [notForSale, setNotForSale] = useState(false);
  const [askingPrice, setAskingPrice] = useState('');
  const [meaningfulness, setMeaningfulness] = useState<number | null>(null);
  const [urgency, setUrgency] = useState<Urgency | null>(null);

  // Slide-in transition (translateX only — no opacity fade, per design)
  const slide = useSharedValue(0);
  useEffect(() => {
    slide.value = 28;
    slide.value = withTiming(0, { duration: 240, easing: Easing.out(Easing.cubic) });
  }, [step]);
  const slideStyle = useAnimatedStyle(() => ({ transform: [{ translateX: slide.value }] }));

  const priceValid = notForSale || Number(askingPrice) > 0;
  const canContinue =
    (step === 0 && wantToDonate !== null) ||
    (step === 1 && priceValid) ||
    (step === 2 && meaningfulness !== null) ||
    (step === 3 && urgency !== null);

  function handleContinue() {
    if (step < TOTAL_STEPS - 1) {
      setStep((s) => s + 1);
      return;
    }
    setAnswers({
      wantToDonate: wantToDonate ?? false,
      askingPrice: notForSale ? null : Number(askingPrice),
      meaningfulness: meaningfulness ?? 3,
      urgency: urgency ?? 'no_rush',
    });
    router.push('/flow/result');
  }

  function handleBack() {
    if (step > 0) setStep((s) => s - 1);
    else router.back();
  }

  return (
    <ThemedView style={styles.container}>
      <View style={styles.progressRow}>
        <ProgressBar progress={(step + 1) / TOTAL_STEPS} />
        <ThemedText style={[Typography.small, styles.stepLabel]} themeColor="textSecondary">
          STEP {step + 1} OF {TOTAL_STEPS}
        </ThemedText>
      </View>

      <Animated.View style={[styles.content, slideStyle]}>
        {step === 0 && (
          <Question
            title={`Do you want to donate this ${itemName}?`}
            subtitle="Donating gives your item a second life with someone who needs it."
          >
            <OptionButton label="Yes, I'd like to donate it" selected={wantToDonate === true} onPress={() => setWantToDonate(true)} />
            <OptionButton label="No, not really" selected={wantToDonate === false} onPress={() => setWantToDonate(false)} />
          </Question>
        )}

        {step === 1 && (
          <Question
            title="How much would you want for it?"
            subtitle="A rough number is fine — it helps us decide between selling and giving it away."
          >
            <Input
              placeholder="$0"
              keyboardType="numeric"
              value={askingPrice}
              editable={!notForSale}
              onChangeText={(t) => setAskingPrice(t.replace(/[^0-9.]/g, ''))}
              containerStyle={styles.priceInput}
            />
            <OptionButton
              label="Not for sale"
              sublabel="I'd rather give it away or toss it"
              selected={notForSale}
              onPress={() => setNotForSale((v) => !v)}
            />
          </Question>
        )}

        {step === 2 && (
          <Question
            title="Is this item meaningful to you?"
            subtitle="Sentimental value can change what you'll want to do with it."
          >
            <View style={styles.scaleRow}>
              {[1, 2, 3, 4, 5].map((n) => (
                <ScalePill key={n} value={n} selected={meaningfulness === n} onPress={() => setMeaningfulness(n)} />
              ))}
            </View>
            <View style={styles.scaleLabels}>
              <ThemedText style={Typography.small} themeColor="textSecondary">Not at all</ThemedText>
              <ThemedText style={Typography.small} themeColor="textSecondary">Very much</ThemedText>
            </View>
          </Question>
        )}

        {step === 3 && (
          <Question
            title="How soon do you need to deal with it?"
            subtitle="Timing affects whether it's worth waiting for a buyer."
          >
            <OptionButton label="This week" sublabel="I want it gone soon" selected={urgency === 'this_week'} onPress={() => setUrgency('this_week')} />
            <OptionButton label="This month" sublabel="No big rush" selected={urgency === 'this_month'} onPress={() => setUrgency('this_month')} />
            <OptionButton label="No rush" sublabel="I can wait for the right option" selected={urgency === 'no_rush'} onPress={() => setUrgency('no_rush')} />
          </Question>
        )}
      </Animated.View>

      <View style={styles.footer}>
        <Button title="Back" variant="ghost" onPress={handleBack} style={styles.backBtn} />
        <Button
          title={step < TOTAL_STEPS - 1 ? 'Continue' : 'See Result'}
          onPress={handleContinue}
          disabled={!canContinue}
          style={styles.continueBtn}
          size="lg"
        />
      </View>
    </ThemedView>
  );
}

function Question({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.question}>
      <ThemedText style={Typography.h2}>{title}</ThemedText>
      <ThemedText style={[Typography.body, styles.subtitle]} themeColor="textSecondary">
        {subtitle}
      </ThemedText>
      <View style={styles.options}>{children}</View>
    </View>
  );
}

function ScalePill({
  value,
  selected,
  onPress,
}: {
  value: number;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <View style={styles.scalePillWrap}>
      <OptionButton label={String(value)} selected={selected} onPress={onPress} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: Spacing.four,
  },
  progressRow: {
    gap: Spacing.one,
    marginBottom: Spacing.four,
  },
  stepLabel: {
    letterSpacing: 1,
  },
  content: {
    flex: 1,
  },
  question: {
    gap: Spacing.two,
  },
  subtitle: {
    marginBottom: Spacing.two,
  },
  options: {
    gap: Spacing.two,
    marginTop: Spacing.two,
  },
  priceInput: {
    marginBottom: Spacing.one,
  },
  scaleRow: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  scalePillWrap: {
    flex: 1,
  },
  scaleLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: Spacing.two,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    paddingTop: Spacing.three,
  },
  backBtn: {
    paddingHorizontal: Spacing.three,
  },
  continueBtn: {
    flex: 1,
  },
});
