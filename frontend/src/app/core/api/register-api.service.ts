import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

// — Types de la page (ou mets-les dans un dossier models si tu préfères)
export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  birth_date: string; // YYYY-MM-DD
  bio?: string;
  language_native: string;
  languages_spoken?: string[];
  languages_wanted?: string[];
  consent_given: boolean;
}

export interface AuthResponse {
  id: number;
  email: string;
  access: string;
  refresh: string;
}

// format problem+json simplifié
export interface Problem {
  status: number;
  code: string;
  detail?: string;
  fields?: Array<{ field: string; code: string; params?: Record<string, unknown> }>;
}

@Injectable({ providedIn: 'root' })
export class RegisterApiService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

  register(body: RegisterPayload): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.base}/auth/register/`, body)
      .pipe(
        catchError((err) => throwError(() => (err?.error as Problem) ?? err))
      );
  }
}
