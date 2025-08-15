// Requête envoyée au backend
export type CreateIntentRequest = {
  booking: number; // id de la réservation
};

// Réponse possible : gratuit (free=true) OU payant (client_secret présent)
export type CreateIntentResponse =
  | { free: true; client_secret: null; payment_id: number }
  | { free?: false; client_secret: string; payment_id: number };

// (Optionnel) Type Payment si tu exposes un GET /payments/{id}/ plus tard
export type PaymentStatus = 'pending' | 'succeeded' | 'failed' | 'canceled';
export type Payment = {
  id: number;
  booking: number;
  amount_cents: number;
  currency: string; // 'eur'
  stripe_payment_intent_id?: string | null;
  status: PaymentStatus;
  created_at: string; // ISO
  updated_at: string; // ISO
};

// (Optionnel) garde de validation runtime, utile en debug/tests
export function assertCreateIntentResponse(x: any): asserts x is CreateIntentResponse {
  if (!x || typeof x.payment_id !== 'number') throw new Error('invalid payment_id');
  if (x.free === true) {
    if (x.client_secret !== null) throw new Error('invalid client_secret for free');
  } else {
    if (typeof x.client_secret !== 'string') throw new Error('missing client_secret');
  }
}
