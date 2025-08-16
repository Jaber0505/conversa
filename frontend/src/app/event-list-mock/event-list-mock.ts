import {ChangeDetectionStrategy, Component, inject} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { TPipe } from '@core/i18n';
import {
  ContainerComponent, GridComponent, HeadlineBarComponent,
  CardComponent, BadgeComponent, ButtonComponent
} from '@shared';
import {Router} from "@angular/router";

type EventDto = {
  id: number;
  language: { code: string; name: string };
  title: string;
  venue_name: string;
  city: string;
  address: string;
  datetime_start: string;  // ISO
  max_seats: number;
  price_cents: number;
  organizer: number;
  is_cancelled: boolean;
  created_at: string;
};

const MOCK_EVENTS: EventDto[] = [
  {
    id: 1,
    language: { code: 'fr', name: 'Français' },
    title: 'Atelier Conversation – Débutants',
    venue_name: 'Maison de Quartier',
    city: 'Bruxelles',
    address: 'Rue des Arts 12',
    datetime_start: new Date(Date.now() + 86400000).toISOString(), // +1j
    max_seats: 6,
    price_cents: 1200,
    organizer: 3,
    is_cancelled: false,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    language: { code: 'nl', name: 'Nederlands' },
    title: 'Praatcafé – Intermediate',
    venue_name: 'De Zaal',
    city: 'Gent',
    address: 'Korenmarkt 3',
    datetime_start: new Date(Date.now() + 2 * 86400000).toISOString(),
    max_seats: 8,
    price_cents: 0,
    organizer: 5,
    is_cancelled: false,
    created_at: new Date().toISOString(),
  },
  {
    id: 3,
    language: { code: 'en', name: 'English' },
    title: 'English Club – Advanced',
    venue_name: 'Community Hub',
    city: 'Liège',
    address: 'Place Saint-Lambert 5',
    datetime_start: new Date(Date.now() + 3 * 86400000).toISOString(),
    max_seats: 10,
    price_cents: 1500,
    organizer: 7,
    is_cancelled: true,
    created_at: new Date().toISOString(),
  },
  {
    id: 4,
    language: { code: 'es', name: 'Español' },
    title: 'Tertulia – Conversación',
    venue_name: 'Centro Cultural',
    city: 'Namur',
    address: 'Rue de l’Ange 8',
    datetime_start: new Date(Date.now() + 5 * 86400000).toISOString(),
    max_seats: 6,
    price_cents: 900,
    organizer: 4,
    is_cancelled: false,
    created_at: new Date().toISOString(),
  },
];

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
  events = MOCK_EVENTS;
  private router = inject(Router);
  trackById = (_: number, e: EventDto) => e.id;

  price(e: EventDto) {
    const cents = e.price_cents ?? 0;
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' }).format(cents / 100);
  }
  goTo(evId: number) {
    debugger;
    this.router.navigate(['/', 'fr', 'events', evId]); }
}
