import { ChangeDetectionStrategy, Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
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
import { BookingDetailModalComponent } from '@app/booking-page-detail/booking-detail';
import {HttpErrorResponse} from "@angular/common/http";

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
export class BookingsPageComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private api = inject(BookingsApiService);

  private refresh$ = new Subject<void>();

  lang(): string { return this.route.snapshot.paramMap.get('lang') ?? 'fr'; }

  vm$ = this.refresh$.pipe(
    startWith(void 0),
    switchMap(() =>
      this.api.list().pipe(
        map(res => ({ state: 'ready', items: res.results }) as Vm),
        catchError(() => of({ state: 'error', message: 'bookings.load_error' } as Vm)),
        startWith({ state: 'loading' } as Vm),
      )
    ),
    shareReplay({ bufferSize: 1, refCount: true }),
  );

  ngOnInit(): void {
  }

  dateLabel(iso: string): string {
    try {
      return new Intl.DateTimeFormat('fr-BE', {
        weekday: 'short', day: '2-digit', month: 'short',
        hour: '2-digit', minute: '2-digit',
      }).format(new Date(iso));
    } catch { return iso; }
  }

  badgeVariant(b: Booking): 'accent' | 'danger' {
    const s = String(b.status).toUpperCase();
    return s === 'CONFIRMED' ? 'accent' : 'danger';
  }

  trackById = (_: number, it: Booking) => (it as any).public_id ?? it.id;

  showDetail = false;
  booking: Booking = {} as Booking;

  openDetail(b: Booking) {
    this.booking = b;
    this.showDetail = true;
  }

  refresh() {
    this.refresh$.next();
  }

  cancel(id: string) {
    this.api.cancel(id).subscribe({
      error: (err: HttpErrorResponse) => {
        if (err.status === 409) console.warn('Déjà confirmé: annulation refusée.');
        else console.error('Erreur annulation:', err);
      }
    });
  }
}
