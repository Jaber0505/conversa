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
import {EventsApiService} from "@core/http";
import {toSignal} from "@angular/core/rxjs-interop";
import {filter, map} from "rxjs/operators";


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
  lang = this.route.snapshot.paramMap.get('lang') ?? 'fr';
  id   = Number(this.route.snapshot.paramMap.get('id') ?? '0');
  actionHref = `/${this.lang}/events`;
  private eventsApi = inject(EventsApiService);
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
    }

  }
}
