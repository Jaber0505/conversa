// core/services/storage.service.ts
import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class StorageService {
  setTokens(access: string, refresh: string) {
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
  }
  get access() { return localStorage.getItem('access'); }
  get refresh() { return localStorage.getItem('refresh'); }
  clear() {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
  }
}
