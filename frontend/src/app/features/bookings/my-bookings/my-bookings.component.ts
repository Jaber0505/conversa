import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { TPipe } from '@core/i18n';
import {Booking, EventDto} from '@core/models';
import {BookingsApiService, EventsApiService, PaymentsApiService, GamesApiService} from '@core/http';
import { CurrencyFormatterService, DateFormatterService } from '@app/core/services';

import {
  ContainerComponent, HeadlineBarComponent,
  BadgeComponent, ButtonComponent, EmptyStateComponent
} from '@shared';

import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { take, finalize, forkJoin, of, catchError } from 'rxjs';
import { BookingDetailModalComponent } from '../components/booking-detail/booking-detail.component';

interface BookingWithEvent extends Booking {
  eventObject: EventDto;
}

@Component({
  selector: 'app-my-bookings',
  standalone: true,
  imports: [
    CommonModule, TPipe,
    ContainerComponent, HeadlineBarComponent,
    BadgeComponent, ButtonComponent, EmptyStateComponent,
    BookingDetailModalComponent,
  ],
  templateUrl: './my-bookings.component.html',
  styleUrls: ['./my-bookings.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MyBookingsComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly bookingsApi = inject(BookingsApiService);
  private readonly eventsApiService = inject(EventsApiService);
  private readonly paymentsApi = inject(PaymentsApiService);
  private readonly gamesApi = inject(GamesApiService);
  private readonly loader = inject(BlockingSpinnerService);
  private readonly currencyFormatter = inject(CurrencyFormatterService);
  private readonly dateFormatter = inject(DateFormatterService);

  readonly items = signal<BookingWithEvent[]>([]);
  readonly error = signal<string | null>(null);
  readonly loading = signal<boolean>(false);

  // Sections pour organiser les réservations
  readonly currentBookings = signal<BookingWithEvent[]>([]);
  readonly futureBookings = signal<BookingWithEvent[]>([]);
  readonly pastBookings = signal<BookingWithEvent[]>([]);

  // Pagination
  readonly itemsPerPage = 6;
  readonly currentPage = signal<number>(1);
  readonly futurePage = signal<number>(1);
  readonly pastPage = signal<number>(1);

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

  /**
   * Variante compatible avec le type de <shared-badge>
   * (évite la valeur "neutral" non supportée)
   */
  historyBadge(b: BookingWithEvent): { label: string; variant: 'primary' | 'accent' | 'danger' | 'secondary' | 'tertiary' | 'success' | 'muted' } {
    const base = this.historyReason(b);
    let variant: 'primary' | 'accent' | 'danger' | 'secondary' | 'tertiary' | 'success' | 'muted' = 'muted';
    if (base.variant === 'danger') variant = 'danger';
    else if (base.variant === 'accent') variant = 'accent';
    else variant = 'muted'; // remplace 'neutral'
    // Corrige l'encodage visible dans certains labels
    const label = base.label
      .replace('AnnulǸ', 'Annulé')
      .replace('FinalisǸ', 'Finalisé');
    return { label, variant };
  }

  /**
   * Raison d'apparition dans l'historique
   * - Annulé par l'utilisateur (booking annulé mais événement pas annulé)
   * - Annulé par l'organisateur (événement annulé)
   * - Finalisé (événement terminé)
   */
  historyReason(b: BookingWithEvent): { label: string; variant: 'accent' | 'danger' | 'neutral' } {
    const eventStatus = String(b.eventObject?.status ?? '').toUpperCase();
    const bookingStatus = String(b.status ?? '').toUpperCase();
    const eventStart = new Date(b.eventObject.datetime_start);
    const eventEnd = new Date(eventStart.getTime() + 60 * 60 * 1000);
    const isPast = new Date() > eventEnd;

    if (bookingStatus === 'CANCELLED') {
      if (eventStatus === 'CANCELLED') {
        return { label: "Annulé par l'organisateur", variant: 'danger' };
      }
      return { label: "Annulé par vous", variant: 'danger' };
    }

    if (eventStatus === 'FINISHED' || isPast) {
      return { label: 'Finalisé', variant: 'neutral' };
    }

    return { label: '', variant: 'neutral' };
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
        // Charger les événements pour chaque booking avec gestion d'erreur individuelle
        const eventRequests = res.results.map(booking =>
          this.eventsApiService.get(booking.event).pipe(
            take(1),
            catchError(error => {
              console.warn(`Event ${booking.event} not found (404), skipping`, error);
              return of(null); // Retourner null pour les événements introuvables
            })
          )
        );

        if (eventRequests.length === 0) {
          this.items.set([]);
          this.organizeBookings([]);
          this.error.set(null);
          return;
        }

        forkJoin(eventRequests).subscribe({
          next: (events) => {
            // Filtrer les bookings dont l'événement n'existe plus
            const bookingsWithEvents: BookingWithEvent[] = res.results
              .map((booking, index) => ({
                booking,
                event: events[index]
              }))
              .filter(item => item.event !== null) // Exclure les événements null (404)
              .map(item => ({
                ...item.booking,
                eventObject: item.event!
              }));

            this.items.set(bookingsWithEvents);
            this.organizeBookings(bookingsWithEvents);
            this.error.set(null);
          },
          error: () => {
            this.error.set('bookings.load_error');
          }
        });
      },
      error: () => {
        this.error.set('bookings.load_error');
      },
    });
  }

  /**
   * Organise les réservations en 3 catégories temporelles basées sur l'heure de l'événement
   * - En cours: événements qui commencent dans les 3h ou sont en cours
   * - Futur: événements confirmés qui sont plus tard
   * - Passé: événements annulés ou terminés
   */
  private organizeBookings(bookings: BookingWithEvent[]) {
    const now = new Date();
    const currentBookingsTemp: BookingWithEvent[] = [];
    const futureBookingsTemp: BookingWithEvent[] = [];
    const pastBookingsTemp: BookingWithEvent[] = [];

    bookings.forEach(booking => {
      const eventStart = new Date(booking.eventObject.datetime_start);
      const hoursUntilEvent = (eventStart.getTime() - now.getTime()) / (1000 * 60 * 60);
      const eventEnd = new Date(eventStart.getTime() + 60 * 60 * 1000); // Événement dure 1h
      const isPast = now > eventEnd;

      // Réservations annulées ou événements passés → Historique
      if (booking.status === 'CANCELLED' || isPast) {
        pastBookingsTemp.push(booking);
      }
      // Réservations en attente de paiement → En cours
      else if (booking.status === 'PENDING') {
        currentBookingsTemp.push(booking);
      }
      // Événements qui commencent dans les 3h ou sont en cours → En cours
      else if (booking.status === 'CONFIRMED' && hoursUntilEvent <= 3 && !isPast) {
        currentBookingsTemp.push(booking);
      }
      // Événements confirmés dans le futur → Futur
      else if (booking.status === 'CONFIRMED') {
        futureBookingsTemp.push(booking);
      }
    });

    // Trier par date d'événement
    currentBookingsTemp.sort((a, b) =>
      new Date(a.eventObject.datetime_start).getTime() - new Date(b.eventObject.datetime_start).getTime()
    );
    futureBookingsTemp.sort((a, b) =>
      new Date(a.eventObject.datetime_start).getTime() - new Date(b.eventObject.datetime_start).getTime()
    );
    pastBookingsTemp.sort((a, b) =>
      new Date(b.eventObject.datetime_start).getTime() - new Date(a.eventObject.datetime_start).getTime()
    );

    this.currentBookings.set(currentBookingsTemp);
    this.futureBookings.set(futureBookingsTemp);
    this.pastBookings.set(pastBookingsTemp);
  }

  /**
   * Vérifie si un événement est en cours (a commencé mais n'est pas terminé)
   */
  isEventLive(booking: BookingWithEvent): boolean {
    const now = new Date();
    const eventStart = new Date(booking.eventObject.datetime_start);
    const eventEnd = new Date(eventStart.getTime() + 60 * 60 * 1000); // Événement dure 1h
    return now >= eventStart && now <= eventEnd;
  }

  /**
   * Obtient le temps restant avant l'événement
   */
  getTimeUntilEvent(booking: BookingWithEvent): string {
    const now = new Date();
    const eventStart = new Date(booking.eventObject.datetime_start);
    const diffMs = eventStart.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);

    if (diffHours > 0) {
      return `Dans ${diffHours}h${diffMins % 60 > 0 ? ' ' + (diffMins % 60) + 'min' : ''}`;
    } else if (diffMins > 0) {
      return `Dans ${diffMins} minutes`;
    } else {
      return 'En cours';
    }
  }

  // ============================================================================
  // PAGINATION
  // ============================================================================

  getPaginatedBookings(section: 'current' | 'future' | 'past'): BookingWithEvent[] {
    let bookings: BookingWithEvent[];
    let page: number;

    switch (section) {
      case 'current':
        bookings = this.currentBookings();
        page = this.currentPage();
        break;
      case 'future':
        bookings = this.futureBookings();
        page = this.futurePage();
        break;
      case 'past':
        bookings = this.pastBookings();
        page = this.pastPage();
        break;
    }

    const startIndex = (page - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    return bookings.slice(startIndex, endIndex);
  }

  getTotalPages(section: 'current' | 'future' | 'past'): number {
    let bookings: BookingWithEvent[];

    switch (section) {
      case 'current':
        bookings = this.currentBookings();
        break;
      case 'future':
        bookings = this.futureBookings();
        break;
      case 'past':
        bookings = this.pastBookings();
        break;
    }

    return Math.ceil(bookings.length / this.itemsPerPage);
  }

  changePage(section: 'current' | 'future' | 'past', page: number) {
    switch (section) {
      case 'current':
        this.currentPage.set(page);
        break;
      case 'future':
        this.futurePage.set(page);
        break;
      case 'past':
        this.pastPage.set(page);
        break;
    }
  }

  getPageNumbers(section: 'current' | 'future' | 'past'): number[] {
    const total = this.getTotalPages(section);
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  // ============================================================================
  // ACTIONS
  // ============================================================================

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

  openDetail(b: BookingWithEvent) {
    this._selected.set(b);
    this._selectedEvent.set(b.eventObject);
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

  /**
   * Lancer/rejoindre le jeu de l'événement en cours
   */
  joinEvent(eventId: number) {
    const booking = this.currentBookings().find(b => b.eventObject.id === eventId);
    if (!booking || !booking.eventObject.game_type) {
      // Pas de jeu configuré, rediriger vers les détails de l'événement
      this.router.navigate(['/', this.lang, 'events', eventId]);
      return;
    }

    this.loader.show('Vérification du jeu...');

    // Vérifier s'il existe un jeu actif
    this.gamesApi.getActiveGame(eventId).pipe(
      take(1),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: (activeGame) => {
        // Un jeu actif existe, le rejoindre
        this.router.navigate(['/', this.lang, 'games', activeGame.id]);
      },
      error: (err) => {
        console.error('Error getting active game:', err);
        // Pas de jeu actif ou erreur, rediriger vers les détails de l'événement
        this.router.navigate(['/', this.lang, 'events', eventId]);
      }
    });
  }

  /**
   * Voir les détails de l'événement
   */
  viewEventDetails(eventId: number) {
    this.router.navigate(['/', this.lang, 'events', eventId]);
  }
}
