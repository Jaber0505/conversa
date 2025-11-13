import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '@core/http';
import { Partner } from '@core/models';
import { Paginated } from '@core/models';

export interface PartnersListParams {
  search?: string;
  page?: number;
  page_size?: number;
}

@Injectable({ providedIn: 'root' })
export class PartnersApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  list(params: PartnersListParams = {}): Observable<Paginated<Partner>> {
    let httpParams = new HttpParams();
    if (params.search) {
      httpParams = httpParams.set('search', params.search);
    }
    if (params.page != null) {
      httpParams = httpParams.set('page', String(params.page));
    }
    if (params.page_size != null) {
      httpParams = httpParams.set('page_size', String(params.page_size));
    }
    return this.http.get<Paginated<Partner>>(`${this.base}/partners/`, { params: httpParams });
  }

  get(id: number): Observable<Partner> {
    return this.http.get<Partner>(`${this.base}/partners/${id}/`);
  }

  availability(partnerId: number, date: string): Observable<{ date: string; partner: number; slots: Array<{ time: string; capacity_remaining: number; event_capacity_max: number; can_create: boolean }> }>{
    const params = new HttpParams().set('date', date);
    return this.http.get<{ date: string; partner: number; slots: Array<{ time: string; capacity_remaining: number; event_capacity_max: number; can_create: boolean }> }>(
      `${this.base}/partners/${partnerId}/availability/`,
      { params }
    );
  }
}
