import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Booking, BookingCreate } from '@app/core/models/bookings.model';
import { Paginated } from '@app/core/models/common.model';
import { API_URL } from '@core/http';

@Injectable({ providedIn: 'root' })
export class BookingsApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  // POST /bookings/
  create(payload: BookingCreate) {
    return this.http.post<Booking>(`${this.base}/bookings/`, payload);
  }

  // GET /bookings/mine/
  mine(params?: Record<string, any>) {
    return this.http.get<Paginated<Booking>>(`${this.base}/bookings/mine/`, { params });
  }
}
