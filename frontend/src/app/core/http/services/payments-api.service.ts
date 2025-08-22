import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '@core/http';

export interface CreateCheckoutSessionPayload {
  booking_public_id: string;
  lang: string;            // ex: "fr"
  success_url?: string;    // optionnel
  cancel_url?: string;     // optionnel
}

export interface CheckoutSessionCreated {
  url: string;
  session_id?: string | null;
}

export interface APIError {
  detail: string;
  code?: string;
}

@Injectable({ providedIn: 'root' })
export class PaymentsApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  /**
   * Crée une session Stripe Checkout (TEST).
   * Retourne l’URL Stripe à ouvrir.
   */
  createCheckoutSession(
    payload: CreateCheckoutSessionPayload
  ): Observable<CheckoutSessionCreated> {
    return this.http.post<CheckoutSessionCreated>(
      `${this.base}/payments/checkout-session/`,
      payload
    );
  }
}
