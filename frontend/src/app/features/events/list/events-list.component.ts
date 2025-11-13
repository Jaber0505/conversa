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
import { EventFiltersComponent, EventFilters } from '../components/event-filters/event-filters.component';
import { EventsSortingService, ScoredEvent } from '../services/events-sorting.service';

import { take, finalize, debounceTime } from 'rxjs/operators';
import { fromEvent } from 'rxjs';
import { SelectOption } from '@shared/forms/select/select.component';
import { buildPaginationItems, PaginationItem } from '@shared/utils/pagination';

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
    EventCardComponent,
    EventFiltersComponent,
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
  readonly myEvents = signal<ScoredEvent[]>([]);
  readonly publicEvents = signal<ScoredEvent[]>([]);
  readonly error = signal<string | null>(null);
  readonly isSmartSortActive = signal<boolean>(false);

  // Draft limit tracking
  readonly draftCount = signal<number>(0);
  readonly canCreateEvent = signal<boolean>(true);
  readonly createButtonTooltip = signal<string | undefined>(undefined);

  // Collapse/Expand state
  readonly isMyEventsSectionCollapsed = signal<boolean>(false);

  // Pagination
  readonly myEventsCurrentPage = signal<number>(1);
  readonly publicEventsCurrentPage = signal<number>(1);
  readonly itemsPerPage = signal<number>(9);
  readonly isMobile = signal<boolean>(false);

  // User data
  private currentUserId: number | null = null;
  userCity: string | null = null;
  userTargetLangs: string[] = [];
  userNativeLangs: string[] = [];

  // Filters
  searchInput = '';
  selectedLangCodes: string[] = [];
  langOptions = signal<SelectOption[]>([]);
  allLanguages: Language[] = [];

  // Modal
  confirmPopup = false;
  private selectedEventId?: number;

  // Payment state
  readonly paymentLoadingEventId = signal<number | null>(null);

  // Backend pagination
  private readonly backendPageSize = 20;
  private nextBackendPage: number | null = 1;
  private isLoadingBackendPage = false;
  private pendingNavigation: { section: 'my' | 'public'; page: number } | null = null;
  private allEvents: EventDto[] = [];
  private loadedEventIds = new Set<number>();
  private autoPrefetchNext = false;

  get lang(): string {
    return this.route.snapshot.paramMap.get('lang') ?? 'fr';
  }

  constructor() {
    this.loadData();
    this.detectScreenSize();

    if (typeof window !== 'undefined') {
      fromEvent(window, 'resize')
        .pipe(
          debounceTime(150),
          takeUntilDestroyed(this.destroyRef)
        )
        .subscribe(() => this.detectScreenSize());
    }
  }

  private detectScreenSize(): void {
    if (typeof window === 'undefined') return;

    const isMobile = window.innerWidth <= 768;
    this.isMobile.set(isMobile);
    this.itemsPerPage.set(isMobile ? 6 : 9);
    this.resolvePendingNavigation();
  }

  toggleMyEventsSection(): void {
    this.isMyEventsSectionCollapsed.set(!this.isMyEventsSectionCollapsed());
  }

  private loadData(): void {
    this.languagesApiService.list().pipe(
      take(1),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(paginatedLanguage => {
      this.allLanguages = paginatedLanguage.results;
      this.langOptions.set(langToOptionsSS(this.allLanguages, this.lang));
    });

    if (this.authTokenService.hasAccess()) {
      this.loadUserPreferences();
    }

    this.loadEvents();
  }

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

  private loadEvents(): void {
    this.resetEventsState();
    this.fetchNextEventsPage(true);
  }

  private resetEventsState(): void {
    this.allEvents = [];
    this.loadedEventIds.clear();
    this.nextBackendPage = 1;
    this.pendingNavigation = null;
    this.isLoadingBackendPage = false;
    this.scoredEvents.set([]);
    this.filteredEvents.set([]);
    this.myEvents.set([]);
    this.publicEvents.set([]);
    this.myEventsCurrentPage.set(1);
    this.publicEventsCurrentPage.set(1);
  }

  private fetchNextEventsPage(showLoader = false): void {
    if (this.nextBackendPage == null || this.isLoadingBackendPage) {
      return;
    }

    const currentPage = this.nextBackendPage;
    this.isLoadingBackendPage = true;
    if (showLoader) {
      this.loader.show('loading');
    }

    const params: EventsListParams = {
      page: currentPage,
      page_size: this.backendPageSize
    };

    this.eventsApi.list(params).pipe(
      take(1),
      finalize(() => {
        this.isLoadingBackendPage = false;
        if (showLoader) {
          this.loader.hide();
        }
        if (this.autoPrefetchNext) {
          this.autoPrefetchNext = false;
          this.fetchNextEventsPage();
        }
      }),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (response) => {
        this.error.set(null);
        this.nextBackendPage = response.next ? currentPage + 1 : null;
        this.mergeEvents(response.results);
        this.autoPrefetchNext = !!response.next && !this.pendingNavigation;
      },
      error: () => {
        this.error.set('events.errors.loading_failed');
      }
    });
  }

  private mergeEvents(newEvents: EventDto[]): void {
    if (!newEvents || newEvents.length === 0) {
      this.resolvePendingNavigation();
      return;
    }

    newEvents.forEach(event => {
      if (this.loadedEventIds.has(event.id)) {
        return;
      }
      this.loadedEventIds.add(event.id);
      event.is_cancelled = event.status === 'CANCELLED' || !!event.cancelled_at;
      this.allEvents.push(event);
    });

    if (this.authTokenService.hasAccess()) {
      this.markAlreadyBooked(this.allEvents);
    } else {
      this.applySmartSort(this.allEvents);
    }
  }

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
        if (!events) return;

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
        if (events) {
          this.applySmartSort(events);
        }
      }
    });
  }

  private applySmartSort(events: EventDto[]): void {
    const scored = this.sortingService.sortEvents(events, {
      userCity: this.userCity || undefined,
      userTargetLangs: this.userTargetLangs,
      userNativeLangs: this.userNativeLangs
    });

    this.scoredEvents.set(scored);

    const queryParams = this.route.snapshot.queryParams;
    const searchEvt = this.paramsToEvt(queryParams);
    this.applyFilters(searchEvt);
  }

  private applyFilters(evt?: SearchEvt): void {
    if (evt) {
      this.searchInput = evt.searchInput;
      this.selectedLangCodes = evt.selectedLangCodes;
    }

    let filtered = this.scoredEvents();

    if (this.selectedLangCodes.length > 0) {
      filtered = filtered.filter(({ event }) =>
        this.selectedLangCodes.includes(event.language_code)
      );
    }

    filtered = this.sortingService.filterBySearch(filtered, this.searchInput);

    const myEvts: ScoredEvent[] = [];
    const publicEvts: ScoredEvent[] = [];

    filtered.forEach(se => {
      const status = se.event.status;
      const isCancelled = status === 'CANCELLED' || !!se.event.cancelled_at;
      if (isCancelled) return;

      if (se.event.organizer_id === this.currentUserId) {
        myEvts.push(se);
      } else if (status === 'PUBLISHED') {
        publicEvts.push(se);
      }
    });

    this.myEvents.set(myEvts);
    this.publicEvents.set(publicEvts);
    this.filteredEvents.set(filtered);

    this.updateDraftCount();
    this.resolvePendingNavigation();
  }

  private resolvePendingNavigation(): void {
    if (!this.pendingNavigation) {
      return;
    }

    const { section, page } = this.pendingNavigation;
    const events = section === 'my' ? this.myEvents() : this.publicEvents();
    const itemsNeeded = (page - 1) * this.itemsPerPage() + 1;

    if (events.length >= itemsNeeded || !this.hasMoreBackendPages()) {
      const totalPages = Math.max(1, this.getTotalPages(events));
      const targetPage = Math.min(Math.max(1, page), totalPages);
      this.setSectionPage(section, targetPage);
      this.pendingNavigation = null;
      this.scrollToEventsTop();
      return;
    }

    this.fetchNextEventsPage();
  }

  private hasMoreBackendPages(): boolean {
    return this.nextBackendPage !== null;
  }

  private setSectionPage(section: 'my' | 'public', page: number): void {
    if (section === 'my') {
      this.myEventsCurrentPage.set(page);
    } else {
      this.publicEventsCurrentPage.set(page);
    }
  }

  private scrollToEventsTop(): void {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  private updateDraftCount(): void {
    const drafts = this.myEvents().filter(se => se.event.status === 'DRAFT');
    const count = drafts.length;

    this.draftCount.set(count);

    const canCreate = count < 3;
    this.canCreateEvent.set(canCreate);

    if (!canCreate) {
      this.createButtonTooltip.set('events.create.draft_limit_reached');
    } else {
      this.createButtonTooltip.set(undefined);
    }
  }

  onSearch(evt: SearchEvt): void {
    this.applyFilters(evt);
  }

  onSearchBar(values: Record<string, string | string[]>): void {
    const langs = (values['field0'] as string[] | undefined) ?? [];
    const q = (values['field1'] as string || '').trim();
    this.applyFilters({ searchInput: q, selectedLangCodes: langs });
  }

  onFiltersChanged(filters: EventFilters): void {
    this.searchInput = filters.searchQuery;
    this.selectedLangCodes = filters.languages;
    this.currentFilters = filters;
    this.applyAdvancedFilters();
  }

  private currentFilters: EventFilters | null = null;

  private applyAdvancedFilters(): void {
    if (!this.currentFilters) {
      this.applyFilters();
      return;
    }

    let filtered = this.scoredEvents();

    // Filtre par langue
    if (this.currentFilters.languages.length > 0) {
      filtered = filtered.filter(({ event }) =>
        this.currentFilters!.languages.includes(event.language_code)
      );
    }

    // Filtre par recherche textuelle
    filtered = this.sortingService.filterBySearch(filtered, this.currentFilters.searchQuery);

    // Filtre par difficulté
    if (this.currentFilters.difficulty) {
      filtered = filtered.filter(({ event }) =>
        event.difficulty?.toLowerCase() === this.currentFilters!.difficulty?.toLowerCase()
      );
    }

    // Filtre par date
    if (this.currentFilters.dateFrom) {
      const fromDate = new Date(this.currentFilters.dateFrom);
      filtered = filtered.filter(({ event }) =>
        new Date(event.datetime_start) >= fromDate
      );
    }
    if (this.currentFilters.dateTo) {
      const toDate = new Date(this.currentFilters.dateTo);
      toDate.setHours(23, 59, 59, 999);
      filtered = filtered.filter(({ event }) =>
        new Date(event.datetime_start) <= toDate
      );
    }

    // Filtre par prix
    if (this.currentFilters.priceType === 'free') {
      filtered = filtered.filter(({ event }) => event.price_cents === 0);
    } else if (this.currentFilters.priceType === 'paid') {
      filtered = filtered.filter(({ event }) => event.price_cents > 0);
    }

    // Filtre par disponibilité
    if (this.currentFilters.availability === 'available') {
      filtered = filtered.filter(({ event }) => !event.is_full);
    } else if (this.currentFilters.availability === 'almost_full') {
      filtered = filtered.filter(({ event }) => {
        const max = event.max_participants || 0;
        if (!max) return false;
        const booked = (event as any).booked_seats ?? event.registration_count ?? 0;
        const ratio = booked / max;
        return ratio >= 0.8 && ratio < 1 && !event.is_full;
      });
    }

    // Séparer "mes événements" et "événements publics"
    const myEvts: ScoredEvent[] = [];
    const publicEvts: ScoredEvent[] = [];

    const userId = this.currentUserId;

    for (const s of filtered) {
      const isOrganizer = (s.event as any).organizer_id === userId || s.event.organizer === userId;
      const alreadyBooked = s.event.alreadyBooked || s.event.alreadyRegistered;

      if (isOrganizer || alreadyBooked) {
        myEvts.push(s);
      } else {
        publicEvts.push(s);
      }
    }

    this.myEvents.set(myEvts);
    this.publicEvents.set(publicEvts);
    this.filteredEvents.set(filtered);

    // Réinitialiser la pagination
    this.myEventsCurrentPage.set(1);
    this.publicEventsCurrentPage.set(1);

    this.updateDraftCount();
    this.resolvePendingNavigation();
  }

  resetSearch(): void {
    this.searchInput = '';
    this.selectedLangCodes = [];
    this.applyFilters({ searchInput: '', selectedLangCodes: [] });
  }

  onBookEvent(eventId: number): void {
    const event = this.findEventById(eventId);
    if (event && this.isEventDtoFull(event)) {
      this.error.set('events.detail.event_full');
      setTimeout(() => this.error.set(null), 4000);
      return;
    }
    this.selectedEventId = eventId;
    this.confirmPopup = true;
  }

  onViewDetails(eventId: number): void {
    this.router.navigate(['/', this.lang, 'events', eventId]);
  }

  onCreateEvent(): void {
    this.router.navigate(['/', this.lang, 'events', 'create']);
  }

  onPlayGame(eventId: number): void {
    this.router.navigate(['/', this.lang, 'events', eventId]);
  }

  onPayDraft(eventId: number): void {
    this.loader.show('payments.redirecting');
    this.router.navigate(['/', this.lang, 'events', eventId]);
  }

  closeDialog(): void {
    this.confirmPopup = false;
  }

  onPayDraftNow(eventId: number): void {
    this.paymentLoadingEventId.set(eventId);
    this.loader.show('payments.redirecting');
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
            this.error.set('payments.errors.url_not_found');
          }
        },
        error: () => {
          this.error.set('events.errors.publication_request_failed');
        }
      });
  }

  performPurchase(): void {
    const evId = this.selectedEventId;
    if (!evId) return;
    const event = this.findEventById(evId);
    if (event && this.isEventDtoFull(event)) {
      this.error.set('events.detail.event_full');
      this.closeDialog();
      return;
    }

    this.loader.show('bookings.creating');

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
            this.error.set('payments.errors.session_creation_failed');
          },
        });
      },
      error: () => {
        this.error.set('bookings.errors.creation_failed');
      },
    });
  }

  getSelectedEventPrice(): number {
    if (!this.selectedEventId) return 0;
    const scoredEvent = this.scoredEvents().find(se => se.event.id === this.selectedEventId);
    return scoredEvent?.event.price_cents ?? 0;
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

  getPaginatedEvents(events: ScoredEvent[], section: 'my' | 'public'): ScoredEvent[] {
    const currentPage = section === 'my' ? this.myEventsCurrentPage() : this.publicEventsCurrentPage();
    const startIndex = (currentPage - 1) * this.itemsPerPage();
    const endIndex = startIndex + this.itemsPerPage();
    return events.slice(startIndex, endIndex);
  }

  getTotalPages(events: ScoredEvent[]): number {
    return Math.ceil(events.length / this.itemsPerPage());
  }

  goToPage(page: number, section: 'my' | 'public', _totalEvents: number): void {
    if (page < 1) return;
    this.pendingNavigation = { section, page };
    this.resolvePendingNavigation();
  }

  getPaginationItems(events: ScoredEvent[], section: 'my' | 'public'): PaginationItem[] {
    const totalPages = this.getTotalPages(events);
    const current = section === 'my'
      ? this.myEventsCurrentPage()
      : this.publicEventsCurrentPage();
    return buildPaginationItems(current, totalPages);
  }

  private findEventById(eventId: number): EventDto | undefined {
    const scored = this.scoredEvents().find(se => se.event.id === eventId);
    if (scored) return scored.event;
    const mine = this.myEvents().find(se => se.event.id === eventId);
    if (mine) return mine.event;
    const pub = this.publicEvents().find(se => se.event.id === eventId);
    return pub?.event;
  }

  private isEventDtoFull(event?: EventDto): boolean {
    if (!event) return false;
    const flag = (event as any).is_full;
    if (typeof flag === 'boolean') {
      return flag;
    }
    const max = event.max_participants || 0;
    if (!max) return false;
    const current =
      (event as any).booked_seats ??
      event.registration_count ??
      0;
    return current >= max;
  }

  trackById = (_: number, se: ScoredEvent) => se.event.id;
}
