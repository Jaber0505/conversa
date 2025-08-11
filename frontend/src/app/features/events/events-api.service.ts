import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

export type EventDto = {
  id: number;
  language: 'en' | 'nl' | 'es' | 'fr';
  area: 'center' | 'ixelles' | 'stg';
  start_at: string;       // ISO
  venue_name: string;
  seats_left: number;
  game: 'speed_phrases' | 'topics_mix' | 'role_cards';
};

@Injectable({ providedIn: 'root' })
export class EventsApiService {
  list(): Observable<EventDto[]> {
    // Mock (remplacé plus tard par l’API)
    const data: EventDto[] = [
      {
        id: 1,
        language: 'en',
        area: 'ixelles',
        start_at: '2025-09-18T19:00:00Z',
        venue_name: 'Café Atlas',
        seats_left: 6,
        game: 'speed_phrases',
      },
      {
        id: 2,
        language: 'nl',
        area: 'center',
        start_at: '2025-09-19T18:30:00Z',
        venue_name: 'Bar Noord',
        seats_left: 4,
        game: 'topics_mix',
      },
      {
        id: 3,
        language: 'es',
        area: 'stg',
        start_at: '2025-09-20T20:00:00Z',
        venue_name: 'Casa Latina',
        seats_left: 5,
        game: 'role_cards',
      },
    ];
    return of(data).pipe(delay(250));
  }
}