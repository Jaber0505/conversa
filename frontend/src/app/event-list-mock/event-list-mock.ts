import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import {ActivatedRoute, Router} from '@angular/router';

import {I18nService, TPipe} from '@core/i18n';
import {
  BookingsApiService,
  EventsApiService,
  EventsListParams,
  LanguagesApiService,
  PaymentsApiService
} from '@core/http';
import {Booking, EventDto, langToOptionsSS, Language, Paginated} from '@core/models';

import {
  ContainerComponent, GridComponent,
  CardComponent, BadgeComponent, ButtonComponent, MultiSelectComponent, HeadlineBarComponent
} from '@shared';
import {BlockingSpinnerService} from "@app/core/http/services/spinner-service";
import {ConfirmPurchaseComponent} from "@app/confirm-purchase/confirm-purchase";
import {map, take} from "rxjs/operators";
import {Observable} from "rxjs";
import type {FilterConfig, GenericSearch} from "@shared/forms/search-bar/search-bar.component";
import {SelectOption} from "@shared/forms/select/select.component";

@Component({
  selector: 'app-event-list-mock',
  standalone: true,
  imports: [
    CommonModule, DatePipe, TPipe,
    ContainerComponent, GridComponent,
    CardComponent, BadgeComponent, ButtonComponent, ConfirmPurchaseComponent, MultiSelectComponent, ButtonComponent, HeadlineBarComponent
  ],
  templateUrl: './event-list-mock.html',
  styleUrls: ['./event-list-mock.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class EventListMockComponent {
  private router = inject(Router);
  alreadyBooked = signal(false);
  private eventsApi = inject(EventsApiService);
  private languagesApiService = inject(LanguagesApiService);
  allLanguage: Language[] = [];
  uiLang: string | null = 'fr';

  // 2) Options pour le multi-select
  langOptions = signal<SelectOption[]>([]);

  confirmPopup = false
  ;
  readonly events = signal<EventDto[]>([]);
  readonly eventsCopy = signal<EventDto[]>([]);
  readonly error = signal<string | null>(null);
  private bookingsApiService = inject(BookingsApiService);
  private paymentsApiService = inject(PaymentsApiService);
  // protected readonly event = signal<EventDto | null>(null);
  private eventId?: number;
  constructor(private loader: BlockingSpinnerService) {
    this.uiLang = this.route.snapshot.paramMap.get('lang') ;
    loader.show("loading");
    this.languagesApiService.list().subscribe((paginatedLanguage =>{
      this.allLanguage = paginatedLanguage.results;
      debugger;
      this.langOptions.set(langToOptionsSS(this.allLanguage, this.uiLang!));
    }))
    const vv={} as EventsListParams;
    this.eventsApi.list(vv).subscribe({
      next: (res : Paginated<EventDto>) => {
        this.setAlreadyBooked(res.results).subscribe(finalList => {
          console.log(finalList);
          this.events.set(finalList);
          this.eventsCopy.set(finalList.slice());
        });
        loader.hide();
      },
      error: (err) => {
        console.error('Error while fetching events:', err);
        this.error.set('Erreur lors du chargement des événements.');
        loader.hide();
      }
    });

  }
  setAlreadyBooked(list: EventDto[]): Observable<EventDto[]> {
    return this.bookingsApiService.list().pipe(
      map((bookings: Paginated<Booking>) => {
        bookings.results.forEach(booking => {
          debugger;
          const rr = list.filter(s => s.id === booking.event && booking.status !== "CANCELLED");
          if(rr.length>0)
          rr.at(0)!.alreadyBooked = true;
        });
        return list;
      })
    );
  }

  closeDialog() {
    this.confirmPopup = false;
  }
  private route = inject(ActivatedRoute);
  get lang(): string { return this.route.snapshot.paramMap.get('lang') ?? 'fr'; }
  performPurchase() {
    const evId = this.eventId;
    if (!evId) return;
    this.bookingsApiService.create(evId).pipe(take(1)).subscribe({
      next: (booking) => {
        this.paymentsApiService.createCheckoutSession({
          booking_public_id: booking.public_id,
          lang: this.lang,
        }).pipe(take(1)).subscribe({
          next: (res) => {
            window.location.href = res.url; },
          error: (err) => {
            console.error('Erreur paiement', err);
            this.error.set('Erreur lors de la création de la session de paiement.');
          },
        });
      },
      error: (err) => {
        console.error('Erreur booking', err);
        this.error.set('Erreur lors de la création de la réservation.');
      },
    });
  }
  trackById = (_: number, e: EventDto) => e.id;
  filters: FilterConfig[] = [];

  price(e: EventDto) {
    const cents = e.price_cents ?? 0;
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' })
      .format(cents / 100);
  }

  goTo(evId: number) {
    this.eventId = evId;
    this.confirmPopup = true;
  }
  private readonly i18n = inject(I18nService);
  selectedLangCodes = signal<string[]>([]);
  onCodesChange(codes: string[]) {
    this.selectedLangCodes.set(codes);
  }
  search() {
    const sel = this.selectedLangCodes();
    if (!sel.length) {
      this.events.set(this.eventsCopy());
      return;
    }
    const wanted = new Set(sel.map(s => s.toLowerCase()));
    this.events.set(
      this.eventsCopy().filter(e => {
        const code = (e.language_code ?? '').toLowerCase();
        return code !== '' && wanted.has(code);
      })
    );
  }

}
