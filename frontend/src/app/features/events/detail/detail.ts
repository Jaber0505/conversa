import { Component, OnInit, OnDestroy, inject, signal, Pipe, PipeTransform } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { take, finalize } from 'rxjs/operators';
import { TPipe } from '@core/i18n';
import { EventsApiService, BookingsApiService, PaymentsApiService, AuthApiService, GamesApiService } from '@core/http';
import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { EventDetailDto, EventParticipantDto, EventParticipantsResponse } from '@core/models';
import { ConfirmPurchaseComponent } from '@app/shared/components/modals/confirm-purchase/confirm-purchase.component';
import { HeadlineBarComponent, SHARED_IMPORTS } from '@shared';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Pipe({
  name: 'sanitizeUrl',
  standalone: true
})
export class SanitizeUrlPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);
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
  private authApi = inject(AuthApiService);
  private paymentsApi = inject(PaymentsApiService);
  private gamesApi = inject(GamesApiService);
  private loader = inject(BlockingSpinnerService);

  event = signal<EventDetailDto | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);

  // Source unique: backend
  isOrganizer = signal(false);
  currentUserId = signal<number | null>(null);

  // Modales
  showCancelModal = signal(false);
  cancellingBooking = signal(false);

  organizerPaymentLoading = signal(false);
  showCancelEventModal = signal(false);
  cancellingEvent = signal(false);
  deletingDraft = signal(false);
  startingGame = signal(false);

  // Cached button state to avoid infinite recalculation
  actionButtonState = signal<'organizer-draft-pay' | 'organizer-draft-delete' | 'organizer-published-cancel' |
    'organizer-published-soon' | 'organizer-pending' |
    'organizer-play' | 'user-play' |
    'user-book' | 'user-pay' | 'user-cancel' |
    'user-starting-soon' | 'event-full' | 'event-cancelled' | 'event-finished' | null>(null);

  participants = signal<EventParticipantDto[]>([]);
  participantsLoading = signal(false);
  participantsError = signal<string | null>(null);

  readonly CANCELLATION_DEADLINE_HOURS = 3;

  private visibilityChangeHandler: (() => void) | null = null;

  ngOnInit(): void {
    this.authApi.me().pipe(take(1)).subscribe({
      next: (me) => {
        this.currentUserId.set(me?.id ?? null);
        const evt = this.event();
        if (evt) this.updateIsOrganizer(evt);
      },
      error: () => {}
    });

    const eventId = this.route.snapshot.paramMap.get('id');
    if (eventId) {
      const id = +eventId;
      this.loadEvent(id);
      this.setupAutoRefresh(id);
    } else {
      this.error.set('events.detail.not_found');
      this.loading.set(false);
    }
  }

  private setupAutoRefresh(eventId: number): void {
    this.visibilityChangeHandler = () => {
      if (document.visibilityState === 'visible') {
        this.loadEvent(eventId);
      }
    };
    document.addEventListener('visibilitychange', this.visibilityChangeHandler);
  }

  ngOnDestroy(): void {
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
        const eventData = event as EventDetailDto;
        this.event.set(eventData);
        this.loadParticipants(id);
        this.updateIsOrganizer(eventData);
        this.updateActionButtonState();
      },
      error: (err: any) => {
        console.error('Error loading event:', err);
        // Rediriger vers la connexion si non authentifié
        const status = err?.status ?? err?.statusCode;
        if (status === 401 || status === 403) {
          this.router.navigate(['/', this.getLang(), 'auth', 'login']);
          return;
        }
        // 404 => not found, sinon erreur générique
        this.error.set(status === 404 ? 'events.detail.not_found' : 'events.detail.error');
      }
    });
  }

  private loadParticipants(eventId: number): void {
    if (!eventId) return;
    this.participantsLoading.set(true);
    this.participantsError.set(null);
    this.participants.set([]);
    this.eventsApi.getParticipants(eventId).pipe(
      take(1),
      finalize(() => this.participantsLoading.set(false))
    ).subscribe({
      next: (response: EventParticipantsResponse) => {
        this.participants.set(response?.participants ?? []);
      },
      error: (err) => {
        console.error('Error loading participants:', err);
        const status = err?.status ?? err?.statusCode;
        if (status === 403) {
          this.participantsError.set('events.detail.participants_forbidden');
        } else {
          this.participantsError.set('events.detail.participants_error');
        }
        this.participants.set([]);
      }
    });
  }

  private updateIsOrganizer(eventData: EventDetailDto | null): void {
    if (!eventData) { this.isOrganizer.set(false); return; }
    const userId = this.currentUserId();
    const organizerId = (eventData as any).organizer_id ?? (eventData as any).organizer;
    this.isOrganizer.set(!!userId && organizerId === userId);
  }

  private updateActionButtonState(): void {
    const evt = this.event();
    if (!evt) {
      this.actionButtonState.set(null);
      return;
    }

    const status = evt.status;
    if (status === 'FINISHED') {
      this.actionButtonState.set('event-finished');
      return;
    }
    if (status === 'CANCELLED') {
      this.actionButtonState.set('event-cancelled');
      return;
    }

    // Vérifier si l'événement a commencé et si un jeu est configuré
    const now = new Date();
    const eventStart = new Date(evt.datetime_start);
    // TEMPORAIRE : Permet de jouer même si l'événement n'a pas commencé (pour tests)
    const hasStarted = true; // now >= eventStart;
    const hasGameConfigured = !!(evt.game_type);

    const links: any = (evt as any)._links || {};
    const perms: any = (evt as any).permissions || {};
    const isOrganizer = this.isOrganizer();

    if (isOrganizer) {
      if (status === 'DRAFT') {
        const canPublish = !!(links.request_publication || links.pay_and_publish);
        if (canPublish) {
          this.actionButtonState.set('organizer-draft-pay');
          return;
        }
        if (links.delete_draft) {
          this.actionButtonState.set('organizer-draft-delete');
          return;
        }
        this.actionButtonState.set(null);
        return;
      }
      if (status === 'PENDING_CONFIRMATION') {
        this.actionButtonState.set('organizer-pending');
        return;
      }
      if (status === 'PUBLISHED') {
        // Si l'événement a commencé et qu'un jeu est configuré
        if (hasStarted && hasGameConfigured) {
          // Afficher bouton pour lancer ou rejoindre le jeu
          this.actionButtonState.set('organizer-play');
          return;
        }
        if (perms.can_cancel_event || links.cancel) {
          this.actionButtonState.set('organizer-published-cancel');
          return;
        }
        this.actionButtonState.set('organizer-published-soon');
        return;
      }
    }

    if (!isOrganizer && (status === 'DRAFT' || status === 'PENDING_CONFIRMATION')) {
      this.actionButtonState.set(null);
      return;
    }

    if (status === 'PUBLISHED') {
      const myb = (evt as any).my_booking as ({ public_id: string; status: string } | null | undefined);

      // Si l'événement a commencé, le jeu est configuré et démarré, et l'utilisateur a une réservation confirmée
      if (hasStarted && hasGameConfigured && evt.game_started && myb?.status === 'CONFIRMED') {
        this.actionButtonState.set('user-play');
        return;
      }

      if (myb?.status === 'PENDING') {
        this.actionButtonState.set('user-pay');
        return;
      }
      if (myb?.status === 'CONFIRMED') {
        this.actionButtonState.set((evt as any).can_cancel_booking ? 'user-cancel' : 'user-starting-soon');
        return;
      }
      if (this.isEventFull(evt as EventDetailDto)) {
        this.actionButtonState.set('event-full');
        return;
      }
      this.actionButtonState.set(perms.can_book ? 'user-book' : null);
      return;
    }

    this.actionButtonState.set(null);
  }

  formatPrice(cents: number): string {
    const amount = cents / 100;
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' }).format(amount);
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }).format(date);
  }

  formatTime(dateStr: string): string {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' }).format(date);
  }

  formatLanguages(codes?: string[] | null): string {
    if (!codes?.length) return '';
    return codes
      .filter((code) => !!code)
      .map((code) => code!.toUpperCase())
      .join(', ');
  }

  getGoogleMapsUrl(address: string): string {
    const query = encodeURIComponent(address);
    return `https://www.google.com/maps?q=${query}&output=embed`;
  }

  public getAvailabilityPercent(evt: EventDetailDto): number {
    const max = evt.max_participants || evt.partner_capacity || 0;
    if (!max) return 0;
    const current = evt.booked_seats ?? evt.participants_count ?? 0;
    return Math.min(100, Math.round((current / max) * 100));
  }

  public isEventFull(evt: EventDetailDto): boolean {
    if (typeof evt.is_full === 'boolean') {
      return evt.is_full;
    }
    const max = evt.max_participants || evt.partner_capacity || 0;
    if (!max) return false;
    const current = evt.booked_seats ?? evt.participants_count ?? 0;
    return current >= max;
  }

  onRequestPublication(): void {
    const evt = this.event();
    if (!evt || !this.isOrganizer()) return;
    this.organizerPaymentLoading.set(true);
    this.loader.show('Préparation du paiement...');
    this.eventsApi.requestPublication(evt.id, this.getLang()).pipe(
      take(1),
      finalize(() => { this.organizerPaymentLoading.set(false); this.loader.hide(); })
    ).subscribe({
      next: (response) => {
        if (response && response.url) {
          window.location.href = response.url;
        } else {
          alert('URL de paiement indisponible');
        }
      },
      error: (err: any) => {
        console.error('Error requesting publication:', err);
        alert(err?.error?.error || 'Erreur lors de la demande de publication');
      }
    });
  }

  onBook(): void {
    const evt = this.event();
    if (!evt) return;
    if (this.isEventFull(evt)) {
      this.actionButtonState.set('event-full');
      return;
    }
    if (!this.currentUserId()) {
      this.router.navigate(['/', this.getLang(), 'auth', 'login']);
      return;
    }
    this.loader.show('Création de la réservation...');
    this.bookingsApi.create(evt.id).pipe(
      take(1),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: (booking) => {
        this.paymentsApi.createCheckoutSession({ booking_public_id: booking.public_id, lang: this.getLang() })
          .pipe(take(1)).subscribe({
            next: (res) => { window.location.href = res.url; },
            error: (err) => { console.error('Error creating checkout session:', err); alert('Erreur lors de la création de la session de paiement'); },
          });
      },
      error: (err) => { console.error('Error creating booking:', err); alert('Erreur lors de la création de la réservation'); }
    });
  }

  onPay(): void {
    const evt = this.event();
    const myb = (evt as any)?.my_booking as ({ public_id: string; status: string } | null | undefined);
    if (!evt || !myb || myb.status !== 'PENDING') return;
    this.loader.show('Redirection vers le paiement...');
    this.paymentsApi.createCheckoutSession({ booking_public_id: myb.public_id, lang: this.getLang() }).pipe(
      take(1),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: (res) => { window.location.href = res.url; },
      error: (err) => { console.error('Error creating checkout session:', err); alert('Erreur lors de la création de la session de paiement'); },
    });
  }

  openCancelModal(): void { this.showCancelModal.set(true); }
  closeCancelModal(): void { this.showCancelModal.set(false); }

  confirmCancelBooking(): void {
    const evt = this.event();
    const myb = (evt as any)?.my_booking as ({ public_id: string; status: string } | null | undefined);
    if (!evt || !myb || (myb.status !== 'CONFIRMED' && myb.status !== 'PENDING')) return;
    this.cancellingBooking.set(true);
    this.bookingsApi.cancel(myb.public_id).pipe(
      take(1),
      finalize(() => { this.cancellingBooking.set(false); this.showCancelModal.set(false); })
    ).subscribe({
      next: () => {
        const eventId = this.event()?.id;
        if (eventId) this.loadEvent(eventId);
      },
      error: (err) => { console.error('Error cancelling booking:', err); alert('Erreur lors de l\'annulation de la réservation'); }
    });
  }

  goBack(): void { this.router.navigate(['/', this.getLang(), 'events']); }

  onDeleteDraft(): void {
    const evt = this.event();
    if (!evt || !this.isOrganizer()) return;
    if (!confirm('Voulez-vous vraiment supprimer ce brouillon ? Cette action est irréversible.')) return;
    this.deletingDraft.set(true);
    this.loader.show('Suppression du brouillon...');
    this.eventsApi.delete(evt.id).pipe(
      take(1),
      finalize(() => { this.deletingDraft.set(false); this.loader.hide(); })
    ).subscribe({
      next: () => { this.router.navigate(['/', this.getLang(), 'events']); },
      error: (err) => { console.error('Error deleting draft:', err); alert('Erreur lors de la suppression du brouillon'); }
    });
  }

  openCancelEventModal(): void { this.showCancelEventModal.set(true); }
  closeCancelEventModal(): void { this.showCancelEventModal.set(false); }

  onPlayGame(): void {
    const evt = this.event();
    if (!evt || !evt.game_type) return;

    const isOrganizer = this.isOrganizer();

    this.startingGame.set(true);
    this.loader.show('Vérification du jeu...');

    // Toujours vérifier d'abord s'il existe un jeu actif
    this.gamesApi.getActiveGame(evt.id).pipe(
      take(1),
      finalize(() => { this.startingGame.set(false); this.loader.hide(); })
    ).subscribe({
      next: (activeGame) => {
        // Un jeu actif existe, rejoindre IMMÉDIATEMENT
        console.log('Jeu actif trouvé:', activeGame);
        this.router.navigate(['/', this.getLang(), 'games', activeGame.id]);
      },
      error: (err) => {
        console.log('Erreur getActiveGame:', err.status, err);

        // Pas de jeu actif (404) - normal
        if (err.status === 404) {
          console.log('Aucun jeu actif, tentative de création...');
          // Si organisateur, créer un nouveau jeu
          if (isOrganizer) {
            this.createNewGame(evt);
          } else {
            alert('Aucun jeu actif. L\'organisateur doit lancer le jeu.');
          }
        }
        // Erreur de permission (403) ou autre erreur serveur
        else if (err.status === 403) {
          alert('Vous n\'avez pas accès à ce jeu. Assurez-vous d\'être inscrit à l\'événement.');
        }
        // Autres erreurs
        else {
          console.error('Error finding game:', err);
          alert(`Erreur lors de la recherche du jeu (${err.status}). Réessayez.`);
        }
      }
    });
  }

  private createNewGame(evt: any): void {
    this.startingGame.set(true);
    this.loader.show('Lancement du jeu...');

    this.gamesApi.create({
      event_id: evt.id,
      game_type: evt.game_type as any
    }).pipe(
      take(1),
      finalize(() => { this.startingGame.set(false); this.loader.hide(); })
    ).subscribe({
      next: (game) => {
        console.log('Jeu créé avec succès:', game);
        // Recharger l'événement pour mettre à jour game_started
        this.loadEvent(evt.id);
        // Rediriger vers la page du jeu
        this.router.navigate(['/', this.getLang(), 'games', game.id]);
      },
      error: (err) => {
        console.error('Error creating game:', err);

        // Si l'erreur dit qu'un jeu actif existe déjà, essayer de le récupérer
        const errorMsg = err?.error?.error || err?.error?.detail || err?.error?.event;
        if (errorMsg && errorMsg.includes('already has an active game')) {
          console.log('Un jeu actif existe déjà, tentative de récupération...');
          // Réessayer de récupérer le jeu actif
          this.startingGame.set(true);
          this.loader.show('Récupération du jeu...');

          this.gamesApi.getActiveGame(evt.id).pipe(
            take(1),
            finalize(() => { this.startingGame.set(false); this.loader.hide(); })
          ).subscribe({
            next: (activeGame) => {
              console.log('Jeu actif récupéré:', activeGame);
              this.router.navigate(['/', this.getLang(), 'games', activeGame.id]);
            },
            error: (getErr) => {
              console.error('Impossible de récupérer le jeu actif:', getErr);
              alert('Un jeu existe déjà mais impossible de le rejoindre. Contactez le support.');
            }
          });
        } else {
          alert(errorMsg || 'Erreur lors du lancement du jeu');
        }
      }
    });
  }

  confirmCancelEvent(): void {
    const evt = this.event();
    if (!evt || !this.isOrganizer()) return;
    this.cancellingEvent.set(true);
    this.eventsApi.cancel(evt.id).pipe(
      take(1),
      finalize(() => { this.cancellingEvent.set(false); this.showCancelEventModal.set(false); })
    ).subscribe({
      next: () => { this.router.navigate(['/', this.getLang(), 'events']); },
      error: (err) => { console.error('Error cancelling event:', err); alert('Erreur lors de l\'annulation de l\'événement'); }
    });
  }

  private getLang(): string {
    return this.route.snapshot.paramMap.get('lang') || 'fr';
  }
}
