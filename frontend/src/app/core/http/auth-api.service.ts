import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

type LoginReq = { username: string; password: string };
type LoginRes = { access: string; refresh: string };
type RegisterReq = { username: string; email: string; password: string };
type MeRes = { id: number; username: string; email: string };
type RefreshRes = { access: string; refresh?: string };

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private http = inject(HttpClient);
  private base = '/api/v1';

  register(data: RegisterReq) { return this.http.post(`${this.base}/auth/register/`, data); }
  login(data: LoginReq)       { return this.http.post<LoginRes>(`${this.base}/auth/login/`, data); }
  refresh(refresh: string)    { return this.http.post<RefreshRes>(`${this.base}/auth/refresh/`, { refresh }); }
  me()                        { return this.http.get<MeRes>(`${this.base}/users/me/`); }
  logout(refresh: string)     { return this.http.post(`${this.base}/auth/logout/`, { refresh }); }
}
