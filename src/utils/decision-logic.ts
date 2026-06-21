import type { Decision, DecisionAnswers, ItemCondition } from '@/types/item';

export interface DecisionResult {
  decision: Decision;
  rationale: string;
  scores: Record<Decision, number>;
}

/**
 * Weighted scoring model that turns the four decision answers (plus the
 * detected condition) into a DONATE / SELL / DISCARD recommendation.
 *
 * The weights are tuned so that:
 *  - Wanting to donate + no asking price strongly favors DONATE.
 *  - A real asking price with decent condition favors SELL.
 *  - Poor condition pushes toward DISCARD (you can't really sell/donate junk).
 *  - High emotional meaningfulness discourages DISCARD.
 */
export function computeDecision(
  answers: DecisionAnswers,
  condition: ItemCondition
): DecisionResult {
  const scores: Record<Decision, number> = { DONATE: 0, SELL: 0, DISCARD: 0 };

  // 1. Explicit donate intent (a leaning, not an override — a real asking
  // price or poor condition can still outweigh it)
  if (answers.wantToDonate) {
    scores.DONATE += 2;
  } else {
    scores.SELL += 1;
    scores.DISCARD += 1;
  }

  // 2. Asking price
  if (answers.askingPrice == null) {
    // Not for sale → give it away or toss it
    scores.DONATE += 2;
    scores.DISCARD += 1;
  } else if (answers.askingPrice > 0) {
    scores.SELL += 3;
    if (answers.askingPrice >= 100) scores.SELL += 1; // worth the listing effort
  }

  // 3. Meaningfulness (emotional attachment) — discourages tossing
  if (answers.meaningfulness >= 4) {
    scores.DISCARD -= 2;
    scores.DONATE += 1; // pass it to someone who'll value it
  } else if (answers.meaningfulness <= 2) {
    scores.DISCARD += 1;
  }

  // 4. Detected condition
  switch (condition) {
    case 'poor':
      scores.DISCARD += 3;
      scores.SELL -= 2;
      scores.DONATE -= 1;
      break;
    case 'fair':
      scores.DISCARD += 1;
      scores.DONATE += 1;
      break;
    case 'good':
      scores.SELL += 1;
      scores.DONATE += 1;
      break;
    case 'excellent':
      scores.SELL += 2;
      scores.DONATE += 1;
      break;
  }

  // 5. Urgency
  switch (answers.urgency) {
    case 'this_week':
      scores.DISCARD += 1;
      scores.DONATE += 1; // quick drop-off is easy
      break;
    case 'no_rush':
      scores.SELL += 1; // can wait for the right buyer
      break;
  }

  // Pick the winner. Tie-break favors the more positive outcome:
  // DONATE > SELL > DISCARD.
  const order: Decision[] = ['DONATE', 'SELL', 'DISCARD'];
  const decision = order.reduce((best, d) => (scores[d] > scores[best] ? d : best), order[0]);

  return { decision, rationale: buildRationale(decision, answers, condition), scores };
}

function buildRationale(
  decision: Decision,
  answers: DecisionAnswers,
  condition: ItemCondition
): string {
  switch (decision) {
    case 'DONATE':
      if (answers.wantToDonate) {
        return "You'd like to donate it, and it's in good enough shape to give someone else a second life with it.";
      }
      return "It's still usable but not worth selling — donating keeps it out of the landfill and helps someone out.";
    case 'SELL':
      return `It's in ${condition} condition and you'd want about $${answers.askingPrice} for it — listing it is worth your time.`;
    case 'DISCARD':
      if (condition === 'poor') {
        return "It's in poor condition, so reselling or donating isn't realistic. Responsible disposal or recycling is the way to go.";
      }
      return "Based on your answers, letting it go is the most practical choice. Look for recycling options where possible.";
  }
}
