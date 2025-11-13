import { Injectable, inject } from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';
import {
  EventDto,
  EventWrite,
  EventUpdate,
  EventCreatePayload,
  EventDetailDto,
  EventParticipantsResponse
} from '@app/core/models/events.model';
import { CheckoutSessionCreated } from './payments-api.service';
import { Paginated } from '@app/core/models/common.model';
import { API_URL } from '@core/http';
import {Observable} from "rxjs";
export interface EventsListParams {
  partner?: number;       // ex: ?partner=12
  language?: string;      // ex: ?language=fr
  ordering?: string;      // ex: datetime_start,-datetime_start
  page?: number;          // ex: page=2
  page_size?: number;     // ex: page_size=50
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
    if (params?.page != null)     httpParams = httpParams.set('page', String(params.page));
    if (params?.page_size != null) httpParams = httpParams.set('page_size', String(params.page_size));
    return this.http.get<Paginated<EventDto>>(`${this.base}/events/`, { params: httpParams });
  }

  get(id: number) {
    return this.http.get<EventDetailDto>(`${this.base}/events/${id}/`);
  }

  getParticipants(id: number) {
    return this.http.get<EventParticipantsResponse>(`${this.base}/events/${id}/participants/`);
  }

  create(payload: EventWrite | EventCreatePayload) {
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

  /**
   * Annuler complètement un événement (organisateur)
   */
  cancel(id: number) {
    return this.http.post<EventDto>(`${this.base}/events/${id}/cancel/`, {});
  }

  /**
   * Demander la publication (organisateur paie) via alias request-publication.
   * Retourne l'URL Stripe Checkout (nouveau workflow pay-and-publish).
   */
  requestPublication(eventId: number, lang: string): Observable<CheckoutSessionCreated> {
    return this.http.post<CheckoutSessionCreated>(
      `${this.base}/events/${eventId}/request-publication/`,
      { lang }
    );
  }
}
