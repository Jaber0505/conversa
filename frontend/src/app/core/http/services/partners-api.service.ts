import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '@core/http';
import { Partner } from '@core/models';
import { Paginated } from '@core/models';

@Injectable({ providedIn: 'root' })
export class PartnersApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  list(search?: string): Observable<Paginated<Partner>> {
    let params = new HttpParams();
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get<Paginated<Partner>>(`${this.base}/partners/`, { params });
  }

  get(id: number): Observable<Partner> {
    return this.http.get<Partner>(`${this.base}/partners/${id}/`);
  }
}
