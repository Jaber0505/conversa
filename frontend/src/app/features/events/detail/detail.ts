import { Component, OnInit, OnDestroy, inject, signal, Pipe, PipeTransform } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { take, finalize } from 'rxjs/operators';
import { TPipe } from '@core/i18n';
import { EventsApiService, BookingsApiService, PaymentsApiService, AuthApiService } from '@core/http';
import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { EventDetailDto } from '@core/models';
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
        this.updateIsOrganizer(eventData);
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

  private updateIsOrganizer(eventData: EventDetailDto | null): void {
    if (!eventData) { this.isOrganizer.set(false); return; }
    const userId = this.currentUserId();
    const organizerId = (eventData as any).organizer_id ?? (eventData as any).organizer;
    this.isOrganizer.set(!!userId && organizerId === userId);
  }

  getActionButtonState():
    'organizer-draft-pay' | 'organizer-draft-delete' | 'organizer-published-cancel' |
    'organizer-published-soon' | 'organizer-pending' |
    'user-book' | 'user-pay' | 'user-cancel' |
    'user-starting-soon' | 'event-full' | 'event-cancelled' | 'event-finished' | null {
    const evt = this.event();
    if (!evt) return null;
    const status = evt.status;
    if (status === 'FINISHED') return 'event-finished';
    if (status === 'CANCELLED') return 'event-cancelled';
    const links: any = (evt as any)._links || {};
    const perms: any = (evt as any).permissions || {};
    const isOrganizer = this.isOrganizer();
    if (isOrganizer) {
      if (status === 'DRAFT') {
        const canPublish = !!(links.request_publication || links.pay_and_publish);
        if (canPublish) return 'organizer-draft-pay';
        if (links.delete_draft) return 'organizer-draft-delete';
        return null;
      }
      if (status === 'PENDING_CONFIRMATION') return 'organizer-pending';
      if (status === 'PUBLISHED') {
        if (perms.can_cancel_event || links.cancel) return 'organizer-published-cancel';
        return 'organizer-published-soon';
      }
    }
    if (!isOrganizer && (status === 'DRAFT' || status === 'PENDING_CONFIRMATION')) return null;
    if (status === 'PUBLISHED') {
      const myb = (evt as any).my_booking as ({ public_id: string; status: string } | null | undefined);
      if (myb?.status === 'PENDING') return 'user-pay';
      if (myb?.status === 'CONFIRMED') return (evt as any).can_cancel_booking ? 'user-cancel' : 'user-starting-soon';
      if ((evt as any).partner_capacity && (evt as any).participants_count >= (evt as any).partner_capacity) return 'event-full';
      return perms.can_book ? 'user-book' : null;
    }
    return null;
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

  getGoogleMapsUrl(address: string): string {
    const query = encodeURIComponent(address);
    return `https://www.google.com/maps?q=${query}&output=embed`;
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
