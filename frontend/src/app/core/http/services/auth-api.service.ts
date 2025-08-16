import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '@core/http';

type LoginReq = { email: string; password: string };
type LoginRes = { access: string; refresh: string };
export type RegisterFormModel = {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  age: number;
  birthDate?: Date | string | null;
  bio?: string;
  native_langs?: string;
  target_langs?: string[];
  consentGiven?: boolean;
};
type MeRes = { id: number; username: string; email: string };
type RefreshRes = { access: string; refresh?: string };

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  register(data: {
    password: string;
    birth_date: string;
    last_name: string;
    bio: string;
    consent_given: boolean;
    native_langs: string[];
    target_langs: string[];
    first_name: string;
    email: string;

    age: number
  }) { return this.http.post(`${this.base}/auth/register/`, data); }
  login(data: LoginReq)       { return this.http.post<LoginRes>(`${this.base}/auth/login/`, data); }
  refresh(refresh: string)    { return this.http.post<RefreshRes>(`${this.base}/auth/refresh/`, { refresh }); }
  me()                        { return this.http.get<MeRes>(`${this.base}/users/me/`); }
  logout(refresh: string)     { return this.http.post(`${this.base}/auth/logout/`, { refresh }); }
}
