import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { TPipe } from '@core/i18n';
import {
  BookingsApiService,
  EventsApiService,
  EventsListParams,
  LanguagesApiService,
  PaymentsApiService,
  AuthTokenService
} from '@core/http';
import { Booking, EventDto, langToOptionsSS, Language, Paginated } from '@core/models';
import { AuthApiService } from '@core/http';

import { ContainerComponent, BadgeComponent, EmptyStateComponent, HeadlineBarComponent } from '@shared';
import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { ConfirmPurchaseComponent } from '@app/shared/components/modals/confirm-purchase/confirm-purchase.component';
import { SearchBarComponent } from '@app/shared/components/search-bar/search-bar';
import { EventCardComponent } from '../components/event-card/event-card.component';
import { EventsSortingService, ScoredEvent } from '../services/events-sorting.service';

import { map, take, finalize } from 'rxjs/operators';
import { SelectOption } from '@shared/forms/select/select.component';

// Local type for search event payload
type SearchEvt = { searchInput: string; selectedLangCodes: string[] };

@Component({
  selector: 'app-events-list',
  standalone: true,
  imports: [
    CommonModule,
    TPipe,
    ContainerComponent,
    BadgeComponent,
    ConfirmPurchaseComponent,
    SearchBarComponent,
    EventCardComponent,
    // UI
    EmptyStateComponent,
    HeadlineBarComponent
  ],
  templateUrl: './events-list.component.html',
  styleUrls: ['./events-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class EventsListComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly eventsApi = inject(EventsApiService);
  private readonly authApi = inject(AuthApiService);
  private readonly authTokenService = inject(AuthTokenService);
  private readonly languagesApiService = inject(LanguagesApiService);
  private readonly bookingsApiService = inject(BookingsApiService);
  private readonly paymentsApiService = inject(PaymentsApiService);
  private readonly loader = inject(BlockingSpinnerService);
  private readonly sortingService = inject(EventsSortingService);

  // État
  readonly scoredEvents = signal<ScoredEvent[]>([]);
  readonly filteredEvents = signal<ScoredEvent[]>([]);
  readonly myEvents = signal<ScoredEvent[]>([]);        // Événements créés par l'utilisateur
  readonly publicEvents = signal<ScoredEvent[]>([]);    // Événements publics (pas ceux de l'utilisateur)
  readonly error = signal<string | null>(null);
  readonly isSmartSortActive = signal<boolean>(false);

  // ID de l'utilisateur connecté
  private currentUserId: number | null = null;

  // Données utilisateur pour le tri intelligent
  userCity: string | null = null;
  userTargetLangs: string[] = [];
  userNativeLangs: string[] = [];

  // Filtres
  searchInput = '';
  selectedLangCodes: string[] = [];
  langOptions = signal<SelectOption[]>([]);
  allLanguages: Language[] = [];

  // Modal de confirmation
  confirmPopup = false;
  private selectedEventId?: number;

  get lang(): string {
    return this.route.snapshot.paramMap.get('lang') ?? 'fr';
  }

  constructor() {
    this.loadData();
  }

  /**
   * Charge toutes les données nécessaires
   */
  private loadData(): void {
    this.loader.show('loading');

    // Charger les langues disponibles
    this.languagesApiService.list().pipe(take(1)).subscribe(paginatedLanguage => {
      this.allLanguages = paginatedLanguage.results;
      this.langOptions.set(langToOptionsSS(this.allLanguages, this.lang));
    });

    // Charger les données utilisateur si connecté
    if (this.authTokenService.hasAccess()) {
      this.loadUserPreferences();
    }

    // Charger les événements
    this.loadEvents();
  }

  /**
   * Charge les préférences utilisateur pour le tri intelligent
   */
  private loadUserPreferences(): void {
    this.authApi.me().pipe(take(1)).subscribe({
      next: (me) => {
        this.currentUserId = me.id;
        this.userCity = (me.city || '').trim();
        this.userTargetLangs = me.target_langs || [];
        this.userNativeLangs = me.native_langs || [];

        // Activer le tri intelligent si on a des données
        const hasPreferences = !!(this.userCity || this.userTargetLangs.length > 0);
        this.isSmartSortActive.set(hasPreferences);
      },
      error: () => {
        this.currentUserId = null;
        this.userCity = null;
        this.userTargetLangs = [];
        this.userNativeLangs = [];
      }
    });
  }

  /**
   * Charge les événements et applique le tri intelligent
   */
  private loadEvents(): void {
    const params = {} as EventsListParams;

    this.eventsApi.list(params).pipe(
      take(1),
      map(res => res.results),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: (events) => {
        // Calculer is_cancelled pour chaque événement
        events.forEach(event => {
          event.is_cancelled = event.status === 'CANCELLED' || !!event.cancelled_at;
        });

        // Marquer les événements déjà réservés (uniquement si connecté)
        if (this.authTokenService.hasAccess()) {
          this.markAlreadyBooked(events);
        } else {
          this.applySmartSort(events);
        }
      },
      error: (err) => {
        this.error.set('Erreur lors du chargement des événements');
      }
    });
  }

  /**
   * Marque les événements déjà réservés par l'utilisateur
   */
  private markAlreadyBooked(events: EventDto[]): void {
    this.bookingsApiService.list().pipe(take(1)).subscribe({
      next: (bookings: Paginated<Booking>) => {
        bookings.results.forEach(booking => {
          if (booking.status !== 'CANCELLED') {
            const event = events.find(e => e.id === booking.event);
            if (event) {
              event.alreadyBooked = true;
            }
          }
        });
        this.applySmartSort(events);
      },
      error: () => {
        // En cas d'erreur, continuer sans marquer les réservations
        this.applySmartSort(events);
      }
    });
  }

  /**
   * Applique le tri intelligent et met à jour l'affichage
   */
  private applySmartSort(events: EventDto[]): void {
    const scored = this.sortingService.sortEvents(events, {
      userCity: this.userCity || undefined,
      userTargetLangs: this.userTargetLangs,
      userNativeLangs: this.userNativeLangs
    });

    this.scoredEvents.set(scored);

    // Appliquer les filtres depuis les query params
    const queryParams = this.route.snapshot.queryParams;
    const searchEvt = this.paramsToEvt(queryParams);
    this.applyFilters(searchEvt);
  }

  /**
   * Applique les filtres de recherche et de langue
   */
  private applyFilters(evt?: SearchEvt): void {
    if (evt) {
      this.searchInput = evt.searchInput;
      this.selectedLangCodes = evt.selectedLangCodes;
    }

    let filtered = this.scoredEvents();

    // Filtre par langue
    if (this.selectedLangCodes.length > 0) {
      filtered = filtered.filter(({ event }) =>
        this.selectedLangCodes.includes(event.language_code)
      );
    }

    // Filtre par recherche textuelle
    filtered = this.sortingService.filterBySearch(filtered, this.searchInput);

    // Séparer "Mes événements" et "Événements publics"
    const myEvts: ScoredEvent[] = [];
    const publicEvts: ScoredEvent[] = [];

    filtered.forEach(se => {
      if (se.event.organizer_id === this.currentUserId) {
        myEvts.push(se);
      } else if (se.event.status === 'PUBLISHED') {
        publicEvts.push(se);
      }
    });

    this.myEvents.set(myEvts);
    this.publicEvents.set(publicEvts);
    this.filteredEvents.set(filtered);
  }

  /**
   * Gestion des événements de recherche
   */
  onSearch(evt: SearchEvt): void { this.applyFilters(evt); }

  // Nouveau composant search-bar: mappe ses valeurs vers nos filtres
  onSearchBar(values: Record<string, string | string[]>): void {
    // field0 = multiselect (langues), field1 = text input (recherche)
    const langs = (values['field0'] as string[] | undefined) ?? [];
    const q = (values['field1'] as string || '').trim();
    this.applyFilters({ searchInput: q, selectedLangCodes: langs });
  }

  resetSearch(): void {
    this.searchInput = '';
    this.selectedLangCodes = [];
    this.applyFilters({ searchInput: '', selectedLangCodes: [] });
  }

  /**
   * Gestion de la réservation
   */
  onBookEvent(eventId: number): void {
    this.selectedEventId = eventId;
    this.confirmPopup = true;
  }

  /**
   * Navigation vers la page de détails
   */
  onViewDetails(eventId: number): void {
    this.router.navigate(['/', this.lang, 'events', eventId]);
  }

  /**
   * Navigation vers la page de création d'événement
   */
  onCreateEvent(): void {
    this.router.navigate(['/', this.lang, 'events', 'create']);
  }

  /**
   * Payer pour publier un événement brouillon
   */
  onPayDraft(eventId: number): void {
    // L'événement a un booking PENDING pour l'organisateur
    // On doit créer une session de paiement pour ce booking
    this.loader.show('Redirection vers le paiement...');

    // Pour l'instant, on redirige vers la page de détail de l'événement
    // où l'utilisateur pourra payer
    this.router.navigate(['/', this.lang, 'events', eventId]);
  }

  closeDialog(): void {
    this.confirmPopup = false;
  }

  performPurchase(): void {
    const evId = this.selectedEventId;
    if (!evId) return;

    this.loader.show('Création de la réservation...');

    this.bookingsApiService.create(evId).pipe(
      take(1),
      finalize(() => this.loader.hide())
    ).subscribe({
      next: (booking) => {
        this.paymentsApiService.createCheckoutSession({
          booking_public_id: booking.public_id,
          lang: this.lang,
        }).pipe(take(1)).subscribe({
          next: (res) => {
            window.location.href = res.url;
          },
          error: () => {
            this.error.set('Erreur lors de la création de la session de paiement.');
          },
        });
      },
      error: () => {
        this.error.set('Erreur lors de la création de la réservation.');
      },
    });
  }

  /**
   * Obtenir le prix pour le modal de confirmation
   */
  getSelectedEventPrice(): number {
    if (!this.selectedEventId) return 0;
    const scoredEvent = this.scoredEvents().find(se => se.event.id === this.selectedEventId);
    return scoredEvent?.event.price_cents ?? 0;
  }

  /**
   * Convertit les query params en objet de recherche
   */
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

  trackById = (_: number, se: ScoredEvent) => se.event.id;
}
