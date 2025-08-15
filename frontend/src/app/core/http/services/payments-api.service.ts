import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '@core/http';
import {
  CreateIntentRequest,
  CreateIntentResponse,
  assertCreateIntentResponse,
} from '@core/models';
import { tap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class PaymentsApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  // POST /payments/create-intent/
  createIntent(payload: CreateIntentRequest) {
    return this.http
      .post<CreateIntentResponse>(`${this.base}/payments/create-intent/`, payload)
      .pipe(tap(res => assertCreateIntentResponse(res))); // optionnel, sécurise le typage à l’exécution
  }
}
