import { ChangeDetectionStrategy, Component, inject, signal, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

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

import { map, take, finalize, debounceTime } from 'rxjs/operators';
import { fromEvent } from 'rxjs';
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
  private readonly destroyRef = inject(DestroyRef);

  // État
  readonly scoredEvents = signal<ScoredEvent[]>([]);
  readonly filteredEvents = signal<ScoredEvent[]>([]);
  readonly myEvents = signal<ScoredEvent[]>([]);        // Événements créés par l'utilisateur
  readonly publicEvents = signal<ScoredEvent[]>([]);    // Événements publics (pas ceux de l'utilisateur)
  readonly error = signal<string | null>(null);
  readonly isSmartSortActive = signal<boolean>(false);

  // B1: Draft limit tracking
  readonly draftCount = signal<number>(0);              // Nombre de drafts de l'utilisateur
  readonly canCreateEvent = signal<boolean>(true);      // Peut créer un événement (< 3 drafts)
  readonly createButtonTooltip = signal<string | undefined>(undefined);  // Tooltip si limité

  // Collapse/Expand state for "Mes événements" section
  readonly isMyEventsSectionCollapsed = signal<boolean>(false);

  // Pagination - separate for each section
  readonly myEventsCurrentPage = signal<number>(1);
  readonly publicEventsCurrentPage = signal<number>(1);
  readonly itemsPerPage = signal<number>(9); // Will be updated based on screen size
  readonly isMobile = signal<boolean>(false);

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

  // Payment loading state
  readonly paymentLoadingEventId = signal<number | null>(null);

  get lang(): string {
    return this.route.snapshot.paramMap.get('lang') ?? 'fr';
  }

  constructor() {
    this.loadData();
    this.detectScreenSize();

    // Listen to window resize for responsive pagination using RxJS
    // This automatically unsubscribes when component is destroyed
    if (typeof window !== 'undefined') {
      fromEvent(window, 'resize')
        .pipe(
          debounceTime(150), // Debounce to avoid too many calls
          takeUntilDestroyed(this.destroyRef)
        )
        .subscribe(() => this.detectScreenSize());
    }
  }

  /**
   * Détecte la taille de l'écran et ajuste itemsPerPage
   */
  private detectScreenSize(): void {
    if (typeof window === 'undefined') return;

    const isMobile = window.innerWidth <= 768;
    this.isMobile.set(isMobile);
    this.itemsPerPage.set(isMobile ? 6 : 9);
  }

  /**
   * Toggle collapse/expand for "Mes événements" section
   */
  toggleMyEventsSection(): void {
    this.isMyEventsSectionCollapsed.set(!this.isMyEventsSectionCollapsed());
  }

  /**
   * Charge toutes les données nécessaires
   */
  private loadData(): void {
    this.loader.show('loading');

    // Charger les langues disponibles
    this.languagesApiService.list().pipe(
      take(1),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(paginatedLanguage => {
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
    this.authApi.me().pipe(
      take(1),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
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
      finalize(() => this.loader.hide()),
      takeUntilDestroyed(this.destroyRef)
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
    if (!events || events.length === 0) {
      this.applySmartSort(events);
      return;
    }

    this.bookingsApiService.list().pipe(
      take(1),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (bookings: Paginated<Booking>) => {
        if (!events) return; // Safety check in case component is destroyed

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
        if (events) {
          this.applySmartSort(events);
        }
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
      const status = se.event.status;
      const isCancelled = status === 'CANCELLED' || !!se.event.cancelled_at;
      if (isCancelled) return; // Ne pas afficher les événements annulés

      if (se.event.organizer_id === this.currentUserId) {
        // Mes événements: inclure DRAFT / PENDING_CONFIRMATION / PUBLISHED, exclure CANCELLED
        myEvts.push(se);
      } else if (status === 'PUBLISHED') {
        // Public uniquement les publiés
        publicEvts.push(se);
      }
    });

    this.myEvents.set(myEvts);
    this.publicEvents.set(publicEvts);
    this.filteredEvents.set(filtered);

    // B1: Update draft count and create button state
    this.updateDraftCount();
  }

  /**
   * B1: Update draft count and create button availability.
   *
   * Business Rule: Max 3 drafts per organizer.
   */
  private updateDraftCount(): void {
    // Count DRAFT events in myEvents
    const drafts = this.myEvents().filter(se => se.event.status === 'DRAFT');
    const count = drafts.length;

    this.draftCount.set(count);

    // Can create if < 3 drafts
    const canCreate = count < 3;
    this.canCreateEvent.set(canCreate);

    // Set tooltip if disabled
    if (!canCreate) {
      this.createButtonTooltip.set('Vous avez atteint la limite de 3 événements en préparation.');
    } else {
      this.createButtonTooltip.set(undefined);
    }
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

  /**
   * Paiement (Checkout) pour publier un brouillon via l'alias request-publication
   */
  onPayDraftNow(eventId: number): void {
    this.paymentLoadingEventId.set(eventId);
    this.loader.show('Redirection vers le paiement...');
    this.eventsApi.requestPublication(eventId, this.lang)
      .pipe(
        take(1),
        finalize(() => {
          this.loader.hide();
          this.paymentLoadingEventId.set(null);
        }),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe({
        next: (res) => {
          if (res && res.url) {
            window.location.href = res.url;
          } else {
            this.error.set('URL de paiement introuvable.');
          }
        },
        error: () => {
          this.error.set("Impossible de demander la publication.");
        }
      });
  }

  performPurchase(): void {
    const evId = this.selectedEventId;
    if (!evId) return;

    this.loader.show('Création de la réservation...');

    this.bookingsApiService.create(evId).pipe(
      take(1),
      finalize(() => this.loader.hide()),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (booking) => {
        this.paymentsApiService.createCheckoutSession({
          booking_public_id: booking.public_id,
          lang: this.lang,
        }).pipe(
          take(1),
          takeUntilDestroyed(this.destroyRef)
        ).subscribe({
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

  /**
   * Obtient les événements paginés pour l'affichage
   */
  getPaginatedEvents(events: ScoredEvent[], section: 'my' | 'public'): ScoredEvent[] {
    const currentPage = section === 'my' ? this.myEventsCurrentPage() : this.publicEventsCurrentPage();
    const startIndex = (currentPage - 1) * this.itemsPerPage();
    const endIndex = startIndex + this.itemsPerPage();
    return events.slice(startIndex, endIndex);
  }

  /**
   * Calcule le nombre total de pages
   */
  getTotalPages(events: ScoredEvent[]): number {
    return Math.ceil(events.length / this.itemsPerPage());
  }

  /**
   * Change de page
   */
  goToPage(page: number, section: 'my' | 'public', totalEvents: number): void {
    const totalPages = Math.ceil(totalEvents / this.itemsPerPage());
    if (page >= 1 && page <= totalPages) {
      if (section === 'my') {
        this.myEventsCurrentPage.set(page);
      } else {
        this.publicEventsCurrentPage.set(page);
      }
      // Scroll to top of events section
      if (typeof window !== 'undefined') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  }

  /**
   * Génère un tableau de numéros de pages pour l'affichage
   */
  getPageNumbers(events: ScoredEvent[], section: 'my' | 'public'): number[] {
    const totalPages = this.getTotalPages(events);
    const current = section === 'my' ? this.myEventsCurrentPage() : this.publicEventsCurrentPage();
    const pages: number[] = [];

    // Always show first page
    pages.push(1);

    // Show pages around current page
    for (let i = Math.max(2, current - 1); i <= Math.min(totalPages - 1, current + 1); i++) {
      if (!pages.includes(i)) {
        pages.push(i);
      }
    }

    // Always show last page
    if (totalPages > 1 && !pages.includes(totalPages)) {
      pages.push(totalPages);
    }

    return pages.sort((a, b) => a - b);
  }

  trackById = (_: number, se: ScoredEvent) => se.event.id;
}
