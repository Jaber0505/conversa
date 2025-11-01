import { Component, OnInit, OnDestroy, inject, signal, Pipe, PipeTransform } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { TPipe } from '@core/i18n';
import { SHARED_IMPORTS } from '@shared';
import { HeadlineBarComponent } from '@shared/layout/headline-bar/headline-bar.component';
import { EventDetailDto, Booking } from '@core/models';
import { EventsApiService, BookingsApiService, AuthTokenService, PaymentsApiService } from '@core/http';
import { take, finalize } from 'rxjs/operators';
import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { ConfirmPurchaseComponent } from '@app/shared/components/modals/confirm-purchase/confirm-purchase.component';

@Pipe({
  name: 'sanitizeUrl',
  standalone: true
})
export class SanitizeUrlPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(url: string): SafeResourceUrl {
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }
}

@Component({
  selector: 'app-event-detail',
  standalone: true,
  imports: [CommonModule, TPipe, SanitizeUrlPipe, ConfirmPurchaseComponent, HeadlineBarComponent, ...SHARED_IMPORTS],
  templateUrl: './detail.html',
  styleUrl: './detail.scss'
})
export class EventDetailComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private eventsApi = inject(EventsApiService);
  private bookingsApi = inject(BookingsApiService);
  private authTokenService = inject(AuthTokenService);
  private paymentsApi = inject(PaymentsApiService);
  private loader = inject(BlockingSpinnerService);

  event = signal<EventDetailDto | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);
  userBooking = signal<Booking | null>(null); // Booking actif de l'utilisateur pour cet événement
  canCancel = signal(false); // Peut annuler dans les 3h avant événement
  showCancelModal = signal(false); // Afficher la modale d'annulation
  cancellingBooking = signal(false); // Annulation en cours

  // Constante pour max participants (cohérent avec backend)
  readonly MAX_PARTICIPANTS = 6;
  readonly CANCELLATION_DEADLINE_HOURS = 3; // Cohérent avec backend

  // Référence à l'écouteur de visibilité pour le nettoyage
  private visibilityChangeHandler: (() => void) | null = null;

  ngOnInit(): void {
    const eventId = this.route.snapshot.paramMap.get('id');
    if (eventId) {
      this.loadEvent(+eventId);

      // Recharger l'événement quand la page devient visible
      // (ex: retour après paiement Stripe)
      this.setupAutoRefresh(+eventId);
    } else {
      this.error.set('events.detail.not_found');
      this.loading.set(false);
    }
  }

  /**
   * Configure le rechargement automatique quand la page devient visible
   * Utile après un paiement Stripe ou quand l'utilisateur revient sur la page
   */
  private setupAutoRefresh(eventId: number): void {
    this.visibilityChangeHandler = () => {
      if (document.visibilityState === 'visible') {
        // Recharger l'événement quand l'utilisateur revient sur la page
        this.loadEvent(eventId);
      }
    };

    // Écouter les changements de visibilité
    document.addEventListener('visibilitychange', this.visibilityChangeHandler);
  }

  ngOnDestroy(): void {
    // Nettoyer l'écouteur pour éviter les fuites de mémoire
    if (this.visibilityChangeHandler) {
      document.removeEventListener('visibilitychange', this.visibilityChangeHandler);
    }
  }

  private loadEvent(id: number): void {
    this.loading.set(true);
    this.error.set(null);

    this.eventsApi.get(id).pipe(
      take(1),
      finalize(() => this.loading.set(false))
    ).subscribe({
      next: (event: any) => {
        // Backend returns EventDetailDto for single event retrieval
        const eventDetail = event as EventDetailDto;
        // Calculer is_cancelled
        eventDetail.is_cancelled = eventDetail.status === 'CANCELLED' || !!eventDetail.cancelled_at;
        this.event.set(eventDetail);

        // Charger le booking de l'utilisateur si connecté
        if (this.authTokenService.hasAccess()) {
          this.loadUserBooking(id);
        }
      },
      error: (err: any) => {
        console.error('Error loading event:', err);
        this.error.set('events.detail.error');
      }
    });
  }

  /**
   * Charge le booking actif de l'utilisateur pour cet événement
   */
  private loadUserBooking(eventId: number): void {
    this.bookingsApi.list().pipe(take(1)).subscribe({
      next: (response) => {
        // Trouver un booking CONFIRMED ou PENDING pour cet événement
        const booking = response.results.find(
          b => b.event === eventId && (b.status === 'CONFIRMED' || b.status === 'PENDING')
        );

        if (booking) {
          this.userBooking.set(booking);
          // Vérifier si l'utilisateur peut annuler (3h avant événement)
          this.checkCancellationDeadline();
        }
      },
      error: (err) => {
        console.error('Error loading user bookings:', err);
      }
    });
  }

  /**
   * Vérifie si l'utilisateur peut annuler son booking (deadline 3h avant événement)
   */
  private checkCancellationDeadline(): void {
    const evt = this.event();
    const booking = this.userBooking();

    if (!evt || !booking || booking.status === 'CANCELLED') {
      this.canCancel.set(false);
      return;
    }

    const eventStart = new Date(evt.datetime_start);
    const now = new Date();
    const hoursUntilEvent = (eventStart.getTime() - now.getTime()) / (1000 * 60 * 60);

    // Peut annuler si plus de 3h avant événement
    this.canCancel.set(hoursUntilEvent > this.CANCELLATION_DEADLINE_HOURS);
  }

  /**
   * Retourne le statut du bouton d'action selon l'état de l'événement et du booking
   */
  getActionButtonState(): 'book' | 'pay' | 'cancel' | 'starting-soon' | 'full' | 'cancelled' {
    const evt = this.event();
    const booking = this.userBooking();

    if (!evt) return 'book';

    // Événement annulé
    if (evt.is_cancelled) return 'cancelled';

    // Utilisateur a un booking PENDING (pas encore payé)
    if (booking && booking.status === 'PENDING') {
      return 'pay';
    }

    // Utilisateur a un booking CONFIRMED (déjà payé)
    if (booking && booking.status === 'CONFIRMED') {
      // Peut annuler si plus de 3h avant événement
      if (this.canCancel()) {
        return 'cancel';
      } else {
        return 'starting-soon';
      }
    }

    // Événement complet
    if (evt.participants_count >= this.MAX_PARTICIPANTS) {
      return 'full';
    }

    // Peut réserver
    return 'book';
  }

  formatPrice(cents: number): string {
    const amount = cents / 100;
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }).format(date);
  }

  formatTime(dateStr: string): string {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  }

  getGoogleMapsUrl(address: string): string {
    const query = encodeURIComponent(address);
    return `https://www.google.com/maps?q=${query}&output=embed`;
  }

  onBook(): void {
    const evt = this.event();
    if (!evt) return;

    // Vérifier si l'utilisateur est connecté
    if (!this.authTokenService.hasAccess()) {
      this.router.navigate(['/', this.getLang(), 'auth', 'login']);
      return;
    }

    this.loader.show('Création de la réservation...');

    // Créer le booking
    this.bookingsApi.create(evt.id).pipe(
      take(1),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: (booking) => {
        // Créer la session de paiement Stripe
        this.paymentsApi.createCheckoutSession({
          booking_public_id: booking.public_id,
          lang: this.getLang(),
        }).pipe(take(1)).subscribe({
          next: (res) => {
            // Rediriger vers Stripe
            window.location.href = res.url;
          },
          error: (err) => {
            console.error('Error creating checkout session:', err);
            alert('Erreur lors de la création de la session de paiement');
          },
        });
      },
      error: (err) => {
        console.error('Error creating booking:', err);
        alert('Erreur lors de la création de la réservation');
      },
    });
  }

  onPay(): void {
    const booking = this.userBooking();
    if (!booking) return;

    this.loader.show('Redirection vers le paiement...');

    // Créer la session de paiement Stripe pour le booking PENDING existant
    this.paymentsApi.createCheckoutSession({
      booking_public_id: booking.public_id,
      lang: this.getLang(),
    }).pipe(
      take(1),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: (res) => {
        // Rediriger vers Stripe
        window.location.href = res.url;
      },
      error: (err) => {
        console.error('Error creating checkout session:', err);
        alert('Erreur lors de la création de la session de paiement');
      },
    });
  }

  openCancelModal(): void {
    this.showCancelModal.set(true);
  }

  closeCancelModal(): void {
    this.showCancelModal.set(false);
  }

  confirmCancelBooking(): void {
    const booking = this.userBooking();
    if (!booking) return;

    this.cancellingBooking.set(true);

    this.bookingsApi.cancel(booking.public_id).pipe(
      take(1),
      finalize(() => {
        this.cancellingBooking.set(false);
        this.showCancelModal.set(false);
      })
    ).subscribe({
      next: () => {
        // Réinitialiser les signaux de booking
        this.userBooking.set(null);
        this.canCancel.set(false);

        // Recharger l'événement pour mettre à jour participants_count
        const eventId = this.event()?.id;
        if (eventId) {
          this.loadEvent(eventId);
        }
      },
      error: (err) => {
        console.error('Error cancelling booking:', err);
        alert('Erreur lors de l\'annulation de la réservation');
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/', this.getLang(), 'events']);
  }

  private getLang(): string {
    return this.route.snapshot.paramMap.get('lang') || 'fr';
  }
}
