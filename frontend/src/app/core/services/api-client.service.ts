import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

type Query = Record<string, unknown>;
type HeadersInit = Record<string, string>;

@Injectable({ providedIn: 'root' })
export class ApiClientService {
  private readonly baseUrl = environment.apiBaseUrl?.replace(/\/+$/, '') ?? '';
  private authToken: string | null = null;

  constructor(private http: HttpClient) {}

  withAuth(token: string | null): this {
    this.authToken = token;
    return this;
  }

  // ---------- Génériques bas niveau ----------
  get<T>(path: string, query?: Query, headers?: HeadersInit) {
    return this.http.get<T>(this.url(path), { headers: this.h(headers), params: this.p(query) });
  }
  post<T, B = unknown>(path: string, body?: B, query?: Query, headers?: HeadersInit) {
    return this.http.post<T>(this.url(path), body ?? null, { headers: this.h(headers, true), params: this.p(query) });
  }
  put<T, B = unknown>(path: string, body?: B, query?: Query, headers?: HeadersInit) {
    return this.http.put<T>(this.url(path), body ?? null, { headers: this.h(headers, true), params: this.p(query) });
  }
  patch<T, B = unknown>(path: string, body?: B, query?: Query, headers?: HeadersInit) {
    return this.http.patch<T>(this.url(path), body ?? null, { headers: this.h(headers, true), params: this.p(query) });
  }
  delete<T>(path: string, query?: Query, headers?: HeadersInit) {
    return this.http.delete<T>(this.url(path), { headers: this.h(headers), params: this.p(query) });
  }

  // ---------- CRUD générique haut niveau ----------
  resource<T>(basePath: string) {
    const path = basePath.replace(/^\/+|\/+$/g, ''); // "users/" -> "users"
    return {
      list: (query?: Query): Observable<{ results?: T[]; count?: number } | T[]> =>
        this.get(`${path}/`, query),
      get: (id: number | string, query?: Query): Observable<T> =>
        this.get(`${path}/${id}/`, query),
      create: <B = Partial<T>>(data: B, query?: Query): Observable<T> =>
        this.post<T, B>(`${path}/`, data, query),
      update: <B = Partial<T>>(id: number | string, data: B, query?: Query): Observable<T> =>
        this.put<T, B>(`${path}/${id}/`, data, query),
      patch:  <B = Partial<T>>(id: number | string, data: B, query?: Query): Observable<T> =>
        this.patch<T, B>(`${path}/${id}/`, data, query),
      remove: (id: number | string, query?: Query): Observable<void> =>
        this.delete<void>(`${path}/${id}/`, query),
    };
  }

  // ---------- Helpers existants (exemples) ----------
  ping() { return this.get<{ status: string; message: string }>('ping'); }

  // ---------- Internes ----------
  private url(path: string): string {
    if (/^https?:\/\//i.test(path)) return path;
    const clean = (path ?? '').replace(/^\/+/, '');
    return `${this.baseUrl}/${clean}`;
  }
  private h(extra?: HeadersInit, json = false): HttpHeaders {
    const base: HeadersInit = {};
    if (json) base['Content-Type'] = 'application/json';
    if (this.authToken) base['Authorization'] = `Bearer ${this.authToken}`;
    const merged = { ...base, ...(extra ?? {}) };
    let headers = new HttpHeaders();
    Object.entries(merged).forEach(([k, v]) => (headers = headers.set(k, v)));
    return headers;
  }
  private p(query?: Query): HttpParams {
    let params = new HttpParams();
    if (!query) return params;
    Object.entries(query).forEach(([k, v]) => {
      if (v === undefined || v === null) return;
      if (Array.isArray(v)) v.forEach((item) => (params = params.append(k, String(item))));
      else params = params.set(k, String(v));
    });
    return params;
  }
}
