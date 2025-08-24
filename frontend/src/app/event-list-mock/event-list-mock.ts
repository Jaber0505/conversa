import {ChangeDetectionStrategy, Component, inject, signal} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import {ActivatedRoute, Params, Router} from '@angular/router';

import {I18nService, TPipe} from '@core/i18n';
import {
  BookingsApiService,
  EventsApiService,
  EventsListParams,
  LanguagesApiService,
  PaymentsApiService
} from '@core/http';
import {Booking, EventDto, langToOptionsSS, Language, Paginated} from '@core/models';
type SearchEvt = { searchInput: string; selectedLangCodes: string[] };
import {
  ContainerComponent, GridComponent,
  CardComponent, BadgeComponent, ButtonComponent, MultiSelectComponent, HeadlineBarComponent, InputComponent
} from '@shared';
import {BlockingSpinnerService} from "@app/core/http/services/spinner-service";
import {ConfirmPurchaseComponent} from "@app/confirm-purchase/confirm-purchase";
import {map, take} from "rxjs/operators";
import {distinctUntilChanged, Observable} from "rxjs";
import type {FilterConfig} from "@shared/forms/search-bar/search-bar.component";
import {SelectOption} from "@shared/forms/select/select.component";
import {FormsModule} from "@angular/forms";
import {SharedSearchPanelComponent} from "@app/shared-search-panel/shared-search-panel";

@Component({
  selector: 'app-event-list-mock',
  standalone: true,
  imports: [
    CommonModule, DatePipe, TPipe,
    ContainerComponent, GridComponent,
    CardComponent, BadgeComponent, ButtonComponent, ConfirmPurchaseComponent, ButtonComponent, FormsModule,SharedSearchPanelComponent
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
  searchInput = "";
  langOptions = signal<SelectOption[]>([]);
  confirmPopup = false;
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
      this.langOptions.set(langToOptionsSS(this.allLanguage, this.uiLang!));
    }))
    const vv={} as EventsListParams;
    this.eventsApi.list(vv).subscribe({
      next: (res : Paginated<EventDto>) => {
        this.setAlreadyBooked(res.results).subscribe(finalList => {
          console.log(finalList);
          this.events.set(finalList);
          this.eventsCopy.set(finalList.slice());
          const evt = this.paramsToEvt(this.route.snapshot.queryParams);
          this.onSearch(evt);
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
  selectedLangCodes : string[]=[];
  onCodesChange(codes: string[]) {
    this.selectedLangCodes = codes;
  }
  onSearch(evt?: { searchInput: string; selectedLangCodes: string[] }) {
    debugger;
    this.searchInput=evt?.searchInput!;
    this.selectedLangCodes=evt?.selectedLangCodes!;
    if ((this.searchInput && this.searchInput.trim() !== '') || this.selectedLangCodes.length > 0) {
      this.events.set(
        this.eventsCopy().filter(e =>
          (this.searchInput && this.searchInput.trim() !== '' ? e.theme.includes(this.searchInput) || e.title.includes(this.searchInput) || e.address.includes(this.searchInput)  : true) &&
          (this.selectedLangCodes.length > 0 ? this.selectedLangCodes.includes(e.language_code) : true)
        )
      );
    } else {
      this.events.set(this.eventsCopy());
    }

  }

  resetSearch() {
    this.searchInput = "";
    this.selectedLangCodes = [];
    this.onSearch({ searchInput: "", selectedLangCodes:[] });
  }
  private paramsToEvt(params: Params): SearchEvt {
    const rawSearch = params['search'];
    const search = Array.isArray(rawSearch) ? (rawSearch[0] ?? '') : (rawSearch ?? '');
    const rawLangs = params['langs'];
    const langsArr = Array.isArray(rawLangs) ? rawLangs : (rawLangs ? [rawLangs] : []);
    const langs = langsArr
      .flatMap(v => (v ?? '').split(','))
      .map(s => s.trim())
      .filter(Boolean);

    return { searchInput: search.trim(), selectedLangCodes: langs };
  }
}
