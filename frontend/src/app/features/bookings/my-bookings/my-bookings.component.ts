import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';

import { TPipe } from '@core/i18n';
import {Booking, EventDto} from '@core/models';
import {BookingsApiService, EventsApiService, PaymentsApiService} from '@core/http';
import { CurrencyFormatterService, DateFormatterService } from '@app/core/services';

import {
  ContainerComponent, GridComponent, HeadlineBarComponent,
  CardComponent, BadgeComponent, ButtonComponent
} from '@shared';

import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { take, finalize } from 'rxjs/operators';
import { BookingDetailModalComponent } from '../components/booking-detail/booking-detail.component';

@Component({
  selector: 'app-my-bookings',
  standalone: true,
  imports: [
    CommonModule, TPipe,
    ContainerComponent, GridComponent, HeadlineBarComponent,
    CardComponent, BadgeComponent, ButtonComponent,
    BookingDetailModalComponent,
  ],
  templateUrl: './my-bookings.component.html',
  styleUrls: ['./my-bookings.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MyBookingsComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly bookingsApi = inject(BookingsApiService);
  private readonly eventsApiService = inject(EventsApiService);
  private readonly paymentsApi = inject(PaymentsApiService);
  private readonly loader = inject(BlockingSpinnerService);
  private readonly currencyFormatter = inject(CurrencyFormatterService);
  private readonly dateFormatter = inject(DateFormatterService);

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
      error: () => {
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
    return this.dateFormatter.formatDateTime(iso);
  }

  price(b: Booking): string {
    const cents = Number((b as any).amount_cents ?? 0);
    return this.currencyFormatter.formatEUR(cents);
  }

  openDetail(b: Booking) {
    this._selected.set(b);
    this.eventsApiService.get(b.event).pipe(take(1)).subscribe({
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
      error: () => {
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
        error: () => { }
      });
  }
}
