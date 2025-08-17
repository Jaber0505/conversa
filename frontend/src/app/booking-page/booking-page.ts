import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, map, of, shareReplay, startWith, switchMap, Subject } from 'rxjs';

import { TPipe } from '@core/i18n';
import {
  ContainerComponent,
  HeadlineBarComponent,
  CardComponent,
  BadgeComponent,
  ButtonComponent,
} from '@shared';

import { Booking } from '@core/models';
import { BookingsApiService } from '@core/http';
import {BookingDetailModalComponent} from "@app/booking-page-detail/booking-detail";

type Vm =
  | { state: 'loading' }
  | { state: 'error'; message?: string }
  | { state: 'ready'; items: Booking[] };

@Component({
  selector: 'app-booking-page',
  standalone: true,
  imports: [
    CommonModule, TPipe,
    ContainerComponent, HeadlineBarComponent, CardComponent, BadgeComponent, ButtonComponent,
    BadgeComponent, BadgeComponent, BadgeComponent, HeadlineBarComponent, BookingDetailModalComponent, // (laisse tel quel)
  ],
  templateUrl: './booking-page.html',
  styleUrls: ['./booking-page.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BookingsPageComponent {
  private route = inject(ActivatedRoute);
  private _api  = inject(BookingsApiService); // conservé pour rebrancher l'API

  private refresh$ = new Subject<void>();

  // ---- MOCK DATA (structure alignée avec Booking)
  bookings: Booking[] = [
    {
      id: 1001,
      event: 1,
      user: 11,
      status: 'confirmed',
      event_start: new Date(Date.now() + 2 * 86400000).toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 1002,
      event: 2,
      user: 11,
      status: 'confirmed',
      event_start: new Date(Date.now() + 4 * 86400000).toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 1003,
      event: 3,
      user: 11,
      status: 'cancelled_user',
      event_start: new Date(Date.now() - 1 * 86400000).toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  lang(): string { return this.route.snapshot.paramMap.get('lang') ?? 'fr'; }

  vm$ = this.refresh$.pipe(
    startWith(void 0),
    switchMap(() =>
      // ⬇️ remplace l'appel API par les mocks
      of(this.bookings).pipe(
        map(items => ({ state: 'ready', items }) as Vm),
        catchError(() => of({ state: 'error', message: 'bookings.load_error' } as Vm)),
        startWith({ state: 'loading' } as Vm),
      )
    ),
    shareReplay({ bufferSize: 1, refCount: true }),
  );

  // Helpers d’affichage
  dateLabel(iso: string): string {
    try {
      return new Intl.DateTimeFormat('fr-BE', {
        weekday: 'short', day: '2-digit', month: 'short',
        hour: '2-digit', minute: '2-digit',
      }).format(new Date(iso));
    } catch { return iso; }
  }

  badgeVariant(b: Booking): 'accent' | 'danger' {
    return b.status === 'confirmed' ? 'accent' : 'danger';
  }

  // canCancel(b: Booking): boolean { return canCancel(b); }
  // cancel(b: Booking) {
  //   if (!this.canCancel(b)) return;
  //   this._api.cancel(b.id).subscribe({
  //     next: () => this.refresh$.next(),
  //     error: () => this.refresh$.next(),
  //   });
  // }

  trackById = (_: number, it: Booking) => it.id;
  showDetail = false;
  booking: Booking = {} as Booking;
}
