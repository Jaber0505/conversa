import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '@core/http';
import {Booking} from "@core/models";

@Injectable({ providedIn: 'root' })
export class BookingsApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL); // ex: http://localhost:8000/api/v1

  // GET /bookings/?event=<id> (optionnel)
  list(params?: { event?: number }): Observable<Booking[]> {
    let httpParams = new HttpParams();
    if (params?.event != null) httpParams = httpParams.set('event', String(params.event));
    return this.http.get<Booking[]>(`${this.base}/bookings/`, { params: httpParams });
  }

  // GET /bookings/:id/
  get(id: number): Observable<Booking> {
    return this.http.get<Booking>(`${this.base}/bookings/${id}/`);
  }

  // POST /bookings/ { event: <id> }
  create(eventId: number): Observable<Booking> {
    return this.http.post<Booking>(`${this.base}/bookings/`, { event: eventId });
  }

  // POST /bookings/:id/cancel/
  cancel(id: number): Observable<Booking> {
    return this.http.post<Booking>(`${this.base}/bookings/${id}/cancel/`, {});
  }
}
