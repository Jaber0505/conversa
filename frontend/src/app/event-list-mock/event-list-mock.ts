import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router } from '@angular/router';

import { TPipe } from '@core/i18n';
import { EventsApiService } from '@core/http';
import { EventDto, Paginated } from '@core/models';

import {
  ContainerComponent, GridComponent, HeadlineBarComponent,
  CardComponent, BadgeComponent, ButtonComponent
} from '@shared';

@Component({
  selector: 'app-event-list-mock',
  standalone: true,
  imports: [
    CommonModule, DatePipe, TPipe,
    ContainerComponent, GridComponent, HeadlineBarComponent,
    CardComponent, BadgeComponent, ButtonComponent
  ],
  templateUrl: './event-list-mock.html',
  styleUrls: ['./event-list-mock.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class EventListMockComponent {
  private router = inject(Router);
  private eventsApi = inject(EventsApiService);

  readonly events = signal<EventDto[]>([]);
  readonly loading = signal<boolean>(true);
  readonly error = signal<string | null>(null);

  constructor() {
    this.eventsApi.list().subscribe({
      next: (res: Paginated<EventDto>) => {
        this.events.set(res.results ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error while fetching events:', err);
        this.error.set('Erreur lors du chargement des événements.');
        this.loading.set(false);
      }
    });
  }

  trackById = (_: number, e: EventDto) => e.id;

  price(e: EventDto) {
    const cents = e.price_cents ?? 0;
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' })
      .format(cents / 100);
  }

  goTo(evId: number) {
    this.router.navigate(['/', 'fr', 'events', evId]);
  }
}
