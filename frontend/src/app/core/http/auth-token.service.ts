import { Injectable } from '@angular/core';

const ACCESS_KEY  = 'access';
const REFRESH_KEY = 'refresh';

@Injectable({ providedIn: 'root' })
export class AuthTokenService {
  get access(): string | null  { return localStorage.getItem(ACCESS_KEY);  }
  get refresh(): string | null { return localStorage.getItem(REFRESH_KEY); }

  save(access: string, refresh?: string | null) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  }

  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }
}
