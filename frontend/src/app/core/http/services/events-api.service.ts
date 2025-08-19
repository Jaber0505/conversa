import { Injectable, inject } from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';
import { EventDto, EventWrite, EventUpdate } from '@app/core/models/events.model';
import { Paginated } from '@app/core/models/common.model';
import { API_URL } from '@core/http';
import {Observable} from "rxjs";
export interface EventsListParams {
  partner?: number;       // ex: ?partner=12
  language?: string;      // ex: ?language=fr
  ordering?: string;      // ex: datetime_start,-datetime_start
}
@Injectable({ providedIn: 'root' })
export class EventsApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  list(params?: EventsListParams): Observable<Paginated<EventDto>> {
    let httpParams = new HttpParams();
    if (params?.partner != null)  httpParams = httpParams.set('partner', String(params.partner));
    if (params?.language)         httpParams = httpParams.set('language', params.language);
    if (params?.ordering)         httpParams = httpParams.set('ordering', params.ordering);
    debugger;
    return this.http.get<Paginated<EventDto>>(`${this.base}/events/`, { params: httpParams });
  }

  get(id: number) {
    return this.http.get<EventDto>(`${this.base}/events/${id}/`);
  }

  create(payload: EventWrite) {
    return this.http.post<EventDto>(`${this.base}/events/`, payload);
  }

  update(id: number, payload: EventWrite) {
    return this.http.put<EventDto>(`${this.base}/events/${id}/`, payload);
  }

  patch(id: number, payload: EventUpdate) {
    return this.http.patch<EventDto>(`${this.base}/events/${id}/`, payload);
  }

  delete(id: number) {
    return this.http.delete<void>(`${this.base}/events/${id}/`);
  }
}
