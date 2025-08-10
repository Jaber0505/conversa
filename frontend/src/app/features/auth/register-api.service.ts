import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export type RegisterPayload = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  bio?: string;
  language_native: string;
  languages_spoken: string[];
  consent_given: boolean;
};

export type RegisterResponse = { id: number; email: string };

@Injectable({ providedIn: 'root' })
export class RegisterApiService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

  register(payload: RegisterPayload) {
    return this.http.post<RegisterResponse>(`${this.base}/auth/register/`, payload);
  }
}
