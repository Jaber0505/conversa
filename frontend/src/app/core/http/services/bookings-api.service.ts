import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '@core/http';
import {Booking, Paginated} from "@core/models";
@Injectable({ providedIn: 'root' })
export class BookingsApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  list(): Observable<Paginated<Booking>> {
    let httpParams = new HttpParams();
    return this.http.get<Paginated<Booking>>(`${this.base}/bookings/`, { params: httpParams });
  }

  get(id: number): Observable<Booking> {
    return this.http.get<Booking>(`${this.base}/bookings/${id}/`);
  }

  create(eventId: number): Observable<Booking> {
    return this.http.post<Booking>(`${this.base}/bookings/`, { event: eventId });
  }

  cancel(id: string): Observable<Booking> {
    return this.http.post<Booking>(`${this.base}/bookings/${id}/cancel/`, {});
  }
}
