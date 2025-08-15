import { Injectable, signal } from '@angular/core';
import { environment } from '@environments';

const ACCESS_KEY  = 'access';
const REFRESH_KEY = 'refresh';

function read(k: string) { try { return localStorage.getItem(k); } catch { return null; } }
function write(k: string, v: string | null) { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} }
function jwtExp(token: string | null): number | null {
  if (!token) return null;
  try { const p = JSON.parse(atob(token.split('.')[1] ?? '')); return typeof p.exp === 'number' ? p.exp : null; } catch { return null; }
}
function nowEpoch(): number { return Math.floor(Date.now() / 1000); }

@Injectable({ providedIn: 'root' })
export class AuthTokenService {
  private accessSig  = signal<string | null>(read(ACCESS_KEY));
  private refreshSig = signal<string | null>(read(REFRESH_KEY));

  get access(): string | null  { return this.accessSig(); }
  get refresh(): string | null { return this.refreshSig(); }

  /** Est-ce qu’un token d’accès existe ? */
  hasAccess(): boolean { return !!this.accessSig(); }

  /** Est-ce que le token d’accès est encore valable (d’après `exp`) ? */
  hasValidAccess(skewSec = 10): boolean {
    const exp = jwtExp(this.accessSig());
    return !!exp && exp - skewSec > nowEpoch();
  }

  /** Sauvegarde et notifie */
  save(access: string, refresh?: string | null) {
    this.accessSig.set(access);
    write(ACCESS_KEY, access);
    if (typeof refresh !== 'undefined') {
      this.refreshSig.set(refresh ?? null);
      write(REFRESH_KEY, refresh ?? null);
    }
  }

  /** Nettoie tout (logout/échec refresh) */
  clear() {
    this.accessSig.set(null);  write(ACCESS_KEY, null);
    this.refreshSig.set(null); write(REFRESH_KEY, null);
  }

  /** Garde les onglets synchronisés (login/logout dans un autre onglet) */
  constructor() {
    window.addEventListener('storage', (e) => {
      if (e.key === ACCESS_KEY)  this.accessSig.set(read(ACCESS_KEY));
      if (e.key === REFRESH_KEY) this.refreshSig.set(read(REFRESH_KEY));
    });
  }
}
