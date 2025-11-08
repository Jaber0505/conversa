import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Paginated, Registration, RegistrationCreatePayload } from '@core/models';
import { API_URL } from '@core/http';

@Injectable({
  providedIn: 'root'
})
export class RegistrationsApiService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_URL);

  /**
   * List my registrations
   */
  list(): Observable<Paginated<Registration>> {
    return this.http.get<Paginated<Registration>>(`${this.base}/registrations/`);
  }

  /**
   * Register for an event (free)
   */
  create(payload: RegistrationCreatePayload): Observable<Registration> {
    return this.http.post<Registration>(`${this.base}/registrations/`, payload);
  }

  /**
   * Cancel registration
   */
  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/registrations/${id}/`);
  }
}
