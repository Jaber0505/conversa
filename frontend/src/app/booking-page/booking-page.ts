import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';

import { TPipe } from '@core/i18n';
import {Booking, EventDto} from '@core/models';
import {BookingsApiService, EventsApiService, PaymentsApiService} from '@core/http';

import {
  ContainerComponent, GridComponent, HeadlineBarComponent,
  CardComponent, BadgeComponent, ButtonComponent
} from '@shared';

import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { HttpErrorResponse } from '@angular/common/http';
import { take, finalize } from 'rxjs/operators';
import { BookingDetailModalComponent } from '@app/booking-page-detail/booking-detail';

@Component({
  selector: 'app-bookings-list',
  standalone: true,
  imports: [
    CommonModule, TPipe,
    ContainerComponent, GridComponent, HeadlineBarComponent,
    CardComponent, BadgeComponent, ButtonComponent,
    BookingDetailModalComponent,
  ],
  templateUrl: './booking-page.html',
  styleUrls: ['./booking-page.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BookingsListComponent {
  private route = inject(ActivatedRoute);
  private bookingsApi = inject(BookingsApiService);
  private eventsApiService = inject(EventsApiService);
  private paymentsApi = inject(PaymentsApiService);
  private loader = inject(BlockingSpinnerService);

  readonly items = signal<Booking[]>([]);
  readonly error = signal<string | null>(null);
  readonly loading = signal<boolean>(false);

  get lang(): string { return this.route.snapshot.paramMap.get('lang') ?? 'fr'; }

  // modal
  showDetail = false;
  private _selected = signal<Booking | null>(null);
  private _selectedEvent = signal<EventDto | null>(null);
  selected = this._selected.asReadonly();
  selectedEvent = this._selectedEvent.asReadonly();

  constructor() {
    this.fetch();
  }

  fetch() {
    this.loading.set(true);
    this.loader.show('Chargement…');
    this.bookingsApi.list().pipe(
      take(1),
      finalize(() => {
        this.loading.set(false);
        this.loader.hide();
      })
    ).subscribe({
      next: (res) => {
        this.items.set(res.results);
        this.error.set(null);
      },
      error: (err: HttpErrorResponse) => {
        console.error('Bookings load error:', err);
        this.error.set('bookings.load_error');
      },
    });
  }

  trackById = (_: number, it: Booking) => (it as any).public_id ?? it.id;

  badgeVariant(b: Booking): 'accent' | 'danger' {
    const s = String(b.status).toUpperCase();
    return s === 'CONFIRMED' ? 'accent' : 'danger';
  }

  dateLabel(iso?: string): string {
    if (!iso) return '—';
    try {
      return new Intl.DateTimeFormat('fr-BE', {
        weekday: 'short', day: '2-digit', month: 'short',
        hour: '2-digit', minute: '2-digit',
      }).format(new Date(iso));
    } catch { return iso; }
  }

  price(b: Booking): string {
    const cents = Number((b as any).amount_cents ?? 0);
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' }).format(cents / 100);
  }

  openDetail(b: Booking) {
    this._selected.set(b);
    this.eventsApiService.get(b.event).subscribe({
      next:(event)=>{
        this._selectedEvent.set(event);
      }
    })
    this.showDetail = true;
  }

  cancel(public_id: string) {
    this.loader.show('Annulation…');
    this.bookingsApi.cancel(public_id).pipe(
      take(1),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: () => this.fetch(),
      error: (err: HttpErrorResponse) => {
        if (err.status === 409) console.warn('Déjà confirmé: annulation refusée.');
        else console.error('Erreur annulation:', err);
        this.fetch();
      }
    });
  }

  pay(public_id: string) {
    this.loader.show('Redirection Stripe…');
    this.paymentsApi.createCheckoutSession({
      booking_public_id: public_id,
      lang: this.lang,
    }).pipe(take(1), finalize(() => this.loader.hide()))
      .subscribe({
        next: (res) => { window.location.href = res.url; },
        error: (err) => { console.error('Erreur paiement', err); }
      });
  }
}
