import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { API_URL } from '@core/http';

export type AuditLog = {
  id: number;
  created_at: string;
  category: string;
  level: string;
  action: string;
  message: string;
  user_email?: string;
  method?: string;
  path?: string;
  status_code?: number;
};

export type Paginated<T> = { count: number; next?: string; previous?: string; results: T[] };

export type AuditListParams = {
  page?: number;
  page_size?: number;
  category?: string;
  level?: string;
  user?: number;
  created_at__gte?: string;
  created_at__lte?: string;
  search?: string;
  method?: string;
  status_code?: number;
};

@Injectable({ providedIn: 'root' })
export class AuditApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  list(params: AuditListParams) {
    let p = new HttpParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') p = p.set(k, String(v));
    });
    return this.http.get<Paginated<AuditLog>>(`${this.base}/audit/`, { params: p });
  }

  stats() {
    return this.http.get<any[]>(`${this.base}/audit/stats/`);
  }

  exportCsv(params: AuditListParams) {
    let p = new HttpParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') p = p.set(k, String(v));
    });
    return this.http.get(`${this.base}/audit/export/`, { params: p, responseType: 'blob' });
  }

  cleanup() {
    return this.http.post<{ status: string; message?: string; output?: string }>(`${this.base}/audit/cleanup/`, {});
  }
}
