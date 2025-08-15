// src/app/core/http/api-url.token.ts
import { InjectionToken } from '@angular/core';
import { environment } from '@environments';

export const API_URL = new InjectionToken<string>('API_URL', {
  providedIn: 'root',
  factory: () => environment.apiBaseUrl.replace(/\/+$/, '')
});
