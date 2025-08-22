import {ChangeDetectionStrategy, Component, inject, OnInit, signal} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TPipe } from '@core/i18n';

import {
  ContainerComponent,
  HeadlineBarComponent,
  CardComponent,
  BadgeComponent,
  ButtonComponent
} from '@shared';
import {ConfirmPurchaseComponent} from "@app/confirm-purchase/confirm-purchase";
import {EventDto} from "@core/models";
import {BookingsApiService, EventsApiService, PaymentsApiService} from "@core/http";
import {toSignal} from "@angular/core/rxjs-interop";
import {filter, map, take} from "rxjs/operators";


@Component({
  selector: 'app-event-detail-mock',
  standalone: true,
  imports: [
    CommonModule, DatePipe, RouterLink, TPipe,
    ContainerComponent, HeadlineBarComponent, CardComponent, BadgeComponent, ButtonComponent, ConfirmPurchaseComponent
  ],
  templateUrl: './event-detail-mock.html',
  styleUrls: ['./event-detail-mock.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class EventDetailMockComponent {
  private route = inject(ActivatedRoute);
  confirmPopup = false;
  alreadyBooked = signal(false);
  lang = this.route.snapshot.paramMap.get('lang') ?? 'fr';
  id   = Number(this.route.snapshot.paramMap.get('id') ?? '0');
  actionHref = `/${this.lang}/events`;
  private eventsApi = inject(EventsApiService);
  private bookingsApiService = inject(BookingsApiService);
  private paymentsApiService = inject(PaymentsApiService);
  readonly error = signal<string | null>(null);

  protected readonly event = signal<EventDto | null>(null);

  price(cents: number) {
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' })
      .format((cents ?? 0) / 100);
  }
  backLink() { return ['/', this.lang, 'events']; }

  closeDialog() {
    this.confirmPopup = false;
  }

  performPurchase() {
    const evId = this.eventId();
    if (!evId) return;

    this.bookingsApiService.create(evId).pipe(take(1)).subscribe({
      next: (booking) => {
        this.paymentsApiService.createCheckoutSession({
          booking_public_id: booking.public_id,
          lang: 'fr',
        }).pipe(take(1)).subscribe({
          next: (res) => {
            debugger; window.location.href = res.url; },
          error: (err) => {
            debugger;
            console.error('Erreur paiement', err);
            this.error.set('Erreur lors de la création de la session de paiement.');
          },
        });
      },
      error: (err) => {
        debugger;
        console.error('Erreur booking', err);
        this.error.set('Erreur lors de la création de la réservation.');
      },
    });
  }


  openPopup() {
    this.confirmPopup = true;
  }
  readonly eventId = toSignal(
    this.route.paramMap.pipe(
      map(p => Number(p.get('id'))),
      filter(id => Number.isFinite(id))
    )
  );
  constructor() {
    const id = this.eventId();
    debugger;
    if (id ) {
      this.eventsApi.get(id).subscribe({
        next: (res: EventDto) => {
          this.event.set(res);
        },
        error: (err) => {
          console.error('Error while fetching events:', err);
          this.error.set('Erreur lors du chargement des événements.');
        }
      });
      this.bookingsApiService.list().pipe(take(1)).subscribe({
        next: (res: any) => {
          // gère les 2 formats: tableau direct ou pagination { results: [...] }
          const items = Array.isArray(res) ? res : res?.results ?? [];
          const exists = items.some((b: any) => b.event === id);
          this.alreadyBooked.set(exists); // ← on met à jour le signal
        },
        error: () => {
          this.alreadyBooked.set(false);
        },
      });
    }

  }
}
