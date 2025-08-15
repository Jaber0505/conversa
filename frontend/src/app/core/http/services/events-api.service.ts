import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Event, EventWrite, EventUpdate } from '@app/core/models/events.model';
import { Paginated } from '@app/core/models/common.model';
import { API_URL } from '@core/http';

@Injectable({ providedIn: 'root' })
export class EventsApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  list(params?: Record<string, any>) { // ajoute filtres/pagination si nécessaire
    return this.http.get<Paginated<Event>>(`${this.base}/events/`, { params });
  }

  get(id: number) {
    return this.http.get<Event>(`${this.base}/events/${id}/`);
  }

  create(payload: EventWrite) {
    return this.http.post<Event>(`${this.base}/events/`, payload);
  }

  update(id: number, payload: EventWrite) {
    return this.http.put<Event>(`${this.base}/events/${id}/`, payload);
  }

  patch(id: number, payload: EventUpdate) {
    return this.http.patch<Event>(`${this.base}/events/${id}/`, payload);
  }

  delete(id: number) {
    return this.http.delete<void>(`${this.base}/events/${id}/`);
  }
}
