export type Decision = 'DONATE' | 'SELL' | 'DISCARD';

export type Urgency = 'this_week' | 'this_month' | 'no_rush';

export type ItemCategory =
  | 'furniture'
  | 'appliance'
  | 'electronics'
  | 'clothing'
  | 'decor'
  | 'sports'
  | 'other';

export type ItemCondition = 'excellent' | 'good' | 'fair' | 'poor';

export interface ItemIdentification {
  itemName: string;
  category: ItemCategory;
  condition: ItemCondition;
  description: string;
}

export interface DecisionAnswers {
  wantToDonate: boolean;
  askingPrice: number | null;
  meaningfulness: number; // 1–5
  urgency: Urgency;
}

export interface SelectedService {
  name: string;
  url: string;
  phone?: string;
  address?: string;
  scheduledDate?: string;
}

export interface Item {
  id: string;
  userId: string;
  photoUrl: string;
  itemName: string;
  category: ItemCategory;
  condition: ItemCondition;
  description: string;
  decision: Decision;
  answers: DecisionAnswers;
  selectedService?: SelectedService;
  createdAt: string;
}
