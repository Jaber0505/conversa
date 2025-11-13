import { Component, OnInit, inject, signal, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { take, finalize, debounceTime } from 'rxjs/operators';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { fromEvent } from 'rxjs';

import { I18nService, LangService, TPipe } from '@core/i18n';
import { EventsApiService, PartnersApiService, LanguagesApiService, PaymentsApiService } from '@core/http';
import { BlockingSpinnerService } from '@app/core/http/services/spinner-service';
import { Partner, Language, EventCreatePayload } from '@core/models';

// Composants Atomic
import { ContainerComponent } from '@shared/layout/container/container.component';
import { SectionComponent } from '@shared/layout/section/section.component';
import { HeadlineBarComponent } from '@shared/layout/headline-bar/headline-bar.component';
import { CardComponent } from '@shared/ui/card/card.component';
import { ButtonComponent } from '@shared/ui/button/button.component';
import { BadgeComponent } from '@shared/ui/badge/badge.component';
import { InputComponent } from '@shared/forms/input/input.component';
import { SelectComponent } from '@shared/forms/select/select.component';
import { PaymentChoiceModalComponent } from '@shared/components/payment-choice-modal/payment-choice-modal.component';
import { buildPaginationItems, PaginationItem } from '@shared/utils/pagination';
@Component({
  selector: 'app-create-event',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TPipe,
    ContainerComponent,
    SectionComponent,
    HeadlineBarComponent,
    CardComponent,
    ButtonComponent,
    BadgeComponent,
    InputComponent,
    SelectComponent,
    PaymentChoiceModalComponent
  ],
  templateUrl: './create.component.html',
  styleUrls: ['./create.component.scss']
})
export class CreateEventComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly eventsApi = inject(EventsApiService);
  private readonly partnersApi = inject(PartnersApiService);
  private readonly languagesApi = inject(LanguagesApiService);
  private readonly paymentsApi = inject(PaymentsApiService);
  private readonly loader = inject(BlockingSpinnerService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly i18n = inject(I18nService);
  private readonly langService = inject(LangService);

  // Étapes
  currentStep = signal(1);
  totalSteps = 5;

  // Données du formulaire
  eventForm!: FormGroup;

  // Données chargées
  partners = signal<Partner[]>([]);
  languages = signal<Language[]>([]);
  partnersLoading = signal(false);

  // Étape 1: Partner sélectionné
  selectedPartner = signal<Partner | null>(null);
  postalCode = '';
  partnersCurrentPage = signal(1);
  partnersItemsPerPage = signal(9);

  // Événement créé
  createdEventId = signal<number | null>(null);
  createdEventPrice = signal<number>(700); // prix par défaut en centimes

  // Modal de paiement
  showPaymentModal = signal(false);

  // Loading states
  loading = signal(false);
  error = signal<string | null>(null);

  // Options pour les selects
  languageOptions = signal<{ value: string; label: string }[]>([]);
  difficultyOptions = signal<{ value: string; label: string }[]>([]);
  gameTypeOptions = signal<{ value: string; label: string }[]>([]);

  // Sélecteur de dates et créneaux (Étape 3)
  availableDays = signal<DaySlot[]>([]);
  availableTimeSlots: string[] = [];
  // Backend-driven availability for the selected day (time -> metadata)
  private slotAvailability: Record<string, { can_create: boolean; capacity_remaining: number; event_capacity_max: number }> = {};

  selectedDay = signal<DaySlot | null>(null);
  selectedTimeSlot = signal<string | null>(null);

  // Timezone Europe/Brussels
  private readonly TIMEZONE = 'Europe/Brussels';
  private readonly partnersBackendPageSize = 20;
  private partnersNextPage: number | null = 1;
  private isLoadingPartnersPage = false;
  private partnerSearchTerm = '';
  private partnerPendingPage: number | null = null;
  private partnersAutoPrefetchNext = false;
  private partnersLoadedIds = new Set<number>();

  constructor() {
    if (typeof window !== 'undefined') {
      this.detectScreenSize();
      fromEvent(window, 'resize')
        .pipe(debounceTime(150), takeUntilDestroyed(this.destroyRef))
        .subscribe(() => this.detectScreenSize());
    }

    // Subscribe to language changes to update translations
    this.langService.lang$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.updateTranslatedOptions();
        this.generateAvailableDays(); // Regenerate days with new language
      });
  }

  ngOnInit(): void {
    this.initForm();
    this.loadLanguages();
    this.loadPartners(true);
    this.updateTranslatedOptions();
    this.generateAvailableDays();
    this.generateTimeSlots();
  }

  private updateTranslatedOptions(): void {
    // Update difficulty options
    this.difficultyOptions.set([
      { value: 'easy', label: this.i18n.t('events.difficulty.easy') },
      { value: 'medium', label: this.i18n.t('events.difficulty.medium') },
      { value: 'hard', label: this.i18n.t('events.difficulty.hard') }
    ]);

    // Update game type options
    this.gameTypeOptions.set([
      { value: 'picture_description', label: this.i18n.t('games.types.picture_description') },
      { value: 'word_association', label: this.i18n.t('games.types.word_association') },
      { value: 'debate', label: this.i18n.t('games.types.debate') },
      { value: 'role_play', label: this.i18n.t('games.types.role_play') }
    ]);

    // Update language options with current language labels
    if (this.languages().length > 0) {
      this.languageOptions.set(this.buildLanguageOptions(this.languages()));
    }
  }

  private detectScreenSize(): void {
    if (typeof window === 'undefined') {
      return;
    }
    const isMobile = window.innerWidth <= 768;
    const nextItemsPerPage = isMobile ? 6 : 9;
    if (this.partnersItemsPerPage() !== nextItemsPerPage) {
      this.partnersItemsPerPage.set(nextItemsPerPage);
      this.partnersCurrentPage.set(1);
    }
    this.resolvePartnerPendingNavigation();
  }

  private initForm(): void {
    this.eventForm = this.fb.group({
      // Étape 1: Partner
      partner: [null, Validators.required],

      // Étape 2: Langue, thème, niveau
      language: [null, Validators.required],
      theme: ['', [Validators.required, Validators.maxLength(120)]],
      difficulty: ['medium', Validators.required],

      // Étape 3: Date et heure
      date: ['', Validators.required],
      time: ['', Validators.required],

      // Étape 4: Configuration du jeu
      gameType: ['picture_description', Validators.required],
      gameDifficulty: ['medium', Validators.required],
    });
  }

  private loadLanguages(): void {
    this.languagesApi.list().pipe(take(1)).subscribe({
      next: (response) => {
        this.languages.set(response.results);
        this.languageOptions.set(this.buildLanguageOptions(response.results));
      },
      error: (err) => {
        console.error('Error loading languages:', err);
      }
    });
  }

  private buildLanguageOptions(list: Language[]): { value: string; label: string }[] {
    return list.map(lang => ({
      value: lang.id.toString(),
      label: this.getLanguageLabel(lang)
    }));
  }

  private loadPartners(reset = false): void {
    if (reset) {
      this.resetPartnerPagination();
    }
    this.fetchNextPartnersPage();
  }

  // Étape 1: Filtrer par code postal via l'API
  onPostalCodeChange(postalCode: string): void {
    this.postalCode = postalCode.trim();
    this.partnerSearchTerm = this.postalCode;
    this.loadPartners(true);
  }

  private resetPartnerPagination(): void {
    this.partners.set([]);
    this.partnersLoadedIds.clear();
    this.partnersNextPage = 1;
    this.partnerPendingPage = null;
    this.partnersAutoPrefetchNext = false;
    this.isLoadingPartnersPage = false;
    this.partnersCurrentPage.set(1);
  }

  private fetchNextPartnersPage(): void {
    if (this.partnersNextPage == null || this.isLoadingPartnersPage) {
      return;
    }

    const currentPage = this.partnersNextPage ?? 1;
    const params = {
      search: this.partnerSearchTerm || undefined,
      page: currentPage,
      page_size: this.partnersBackendPageSize
    };

    this.isLoadingPartnersPage = true;
    this.partnersLoading.set(true);

    this.partnersApi.list(params).pipe(
      take(1),
      finalize(() => {
        this.isLoadingPartnersPage = false;
        this.partnersLoading.set(false);
        if (this.partnersAutoPrefetchNext) {
          this.partnersAutoPrefetchNext = false;
          this.fetchNextPartnersPage();
        }
      })
    ).subscribe({
      next: (response) => {
        this.partnersNextPage = response.next ? currentPage + 1 : null;
        this.mergePartners(response.results);
        this.partnersAutoPrefetchNext = !!response.next && this.partnerPendingPage == null;
      },
      error: (err) => {
        console.error('Error loading partners:', err);
      }
    });
  }

  private mergePartners(newPartners: Partner[]): void {
    if (!newPartners || newPartners.length === 0) {
      this.resolvePartnerPendingNavigation();
      return;
    }

    const updated = [...this.partners()];
    let changed = false;

    newPartners.forEach((partner) => {
      if (this.partnersLoadedIds.has(partner.id)) {
        return;
      }
      this.partnersLoadedIds.add(partner.id);
      updated.push(partner);
      changed = true;
    });

    if (changed) {
      this.partners.set(updated);
    }
    this.resolvePartnerPendingNavigation();
  }

  getPaginatedPartners(): Partner[] {
    const page = this.partnersCurrentPage();
    const itemsPerPage = this.partnersItemsPerPage();
    const startIndex = (page - 1) * itemsPerPage;
    return this.partners().slice(startIndex, startIndex + itemsPerPage);
  }

  getPartnerTotalPages(): number {
    return Math.ceil(this.partners().length / this.partnersItemsPerPage());
  }

  getPartnerPaginationItems(): PaginationItem[] {
    return buildPaginationItems(this.partnersCurrentPage(), this.getPartnerTotalPages());
  }

  goToPartnerPage(page: number): void {
    if (page < 1) return;
    this.partnerPendingPage = page;
    this.resolvePartnerPendingNavigation();
  }

  private resolvePartnerPendingNavigation(): void {
    if (this.partnerPendingPage == null) {
      return;
    }

    const itemsNeeded = this.partnerPendingPage * this.partnersItemsPerPage();
    if (this.partners().length >= itemsNeeded || !this.hasMorePartnerPages()) {
      const totalPages = Math.max(1, this.getPartnerTotalPages());
      const targetPage = Math.min(Math.max(1, this.partnerPendingPage), totalPages);
      this.partnersCurrentPage.set(targetPage);
      this.partnerPendingPage = null;
      return;
    }

    this.fetchNextPartnersPage();
  }

  private hasMorePartnerPages(): boolean {
    return this.partnersNextPage !== null;
  }

  selectPartner(partner: Partner): void {
    this.selectedPartner.set(partner);
    this.eventForm.patchValue({ partner: partner.id });
    // Si un jour est déjà sélectionné, recharger l'availability
    const day = this.selectedDay();
    if (day) {
      this.selectDay(day);
    }
  }

  viewPartnerDetails(partnerId: number, event?: Event): void {
    // Empêcher la sélection de la carte
    if (event) {
      event.stopPropagation();
    }
    // TODO: Implémenter la modal de détails du partner
    console.log('Voir les détails du partner:', partnerId);
    alert(`Les détails du partner ${partnerId} seront affichés dans une future version.`);
  }

  onLanguageChange(value: string | undefined): void {
    if (value) {
      this.eventForm.patchValue({ language: parseInt(value, 10) });
    }
  }

  onDifficultyChange(value: string | undefined): void {
    if (value) {
      this.eventForm.patchValue({ difficulty: value });
    }
  }

  onGameTypeChange(value: string | undefined): void {
    if (value) {
      this.eventForm.patchValue({ gameType: value });
    }
  }

  // Navigation entre étapes
  canGoNext(): boolean {
    switch (this.currentStep()) {
      case 1:
        return !!this.selectedPartner();
      case 2:
        return (this.eventForm.get('language')?.valid ?? false) &&
               (this.eventForm.get('theme')?.valid ?? false) &&
               (this.eventForm.get('difficulty')?.valid ?? false);
      case 3:
        return (this.eventForm.get('date')?.valid ?? false) &&
               (this.eventForm.get('time')?.valid ?? false);
      case 4:
        return (this.eventForm.get('gameType')?.valid ?? false);
      default:
        return false;
    }
  }

  nextStep(): void {
    if (this.canGoNext() && this.currentStep() < this.totalSteps) {
      this.currentStep.update(s => s + 1);
    }
  }

  prevStep(): void {
    if (this.currentStep() > 1) {
      this.currentStep.update(s => s - 1);
    }
  }

  goToStep(step: number): void {
    if (step <= this.currentStep() || this.canGoNext()) {
      this.currentStep.set(step);
    }
  }

  // Étape 4: Création de l'événement avec choix de paiement
  createEvent(): void {
    if (!this.eventForm.valid) {
      this.error.set('events.create.errors.form_required');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.loader.show(this.i18n.t('events.create.loader.creating'));

    const formValue = this.eventForm.value;

    // Construire datetime_start à partir de date et time
    const datetime_start = `${formValue.date}T${formValue.time}:00`;

    // S'assurer que les IDs sont des numbers
    const partnerId = typeof formValue.partner === 'string'
      ? parseInt(formValue.partner, 10)
      : formValue.partner;
    const languageId = typeof formValue.language === 'string'
      ? parseInt(formValue.language, 10)
      : formValue.language;

    const eventData: EventCreatePayload = {
      partner: partnerId,
      language: languageId,
      theme: formValue.theme as string,
      difficulty: formValue.difficulty as string,
      datetime_start: datetime_start,
      game_type: formValue.gameType as string
    };

    console.log('Sending event data:', eventData);

    this.eventsApi.create(eventData).pipe(
      take(1),
      finalize(() => {
        this.loading.set(false);
        this.loader.hide();
      })
    ).subscribe({
      next: (response: any) => {
        // Événement créé en DRAFT
        console.log('Event created in DRAFT:', response);
        this.createdEventId.set(response.id);
        this.createdEventPrice.set(response.price_cents || 700);

        // Afficher le modal de choix de paiement
        this.showPaymentModal.set(true);
      },
      error: (err) => {
        console.error('Error creating event:', err);
        const apiError = err?.error?.error;
        this.error.set(apiError || 'events.create.errors.create_failed');
      }
    });
  }

  /**
   * Gestion du succès du paiement
   */
  onPaymentSuccess(): void {
    this.showPaymentModal.set(false);

    // Rediriger vers la page de détails de l'événement publié
    const eventId = this.createdEventId();
    if (eventId) {
      this.router.navigate(['/', this.getLang(), 'events', eventId]);
    }
  }

  /**
   * Gestion du choix "Payer plus tard"
   */
  onPayLater(): void {
    this.showPaymentModal.set(false);

    // Rediriger vers la page de détails de l'événement en DRAFT
    const eventId = this.createdEventId();
    if (eventId) {
      this.router.navigate(['/', this.getLang(), 'events', eventId]);
    }
  }

  /**
   * Fermeture du modal
   */
  onClosePaymentModal(): void {
    this.showPaymentModal.set(false);

    // Rediriger vers la liste des événements
    this.router.navigate(['/', this.getLang(), 'events']);
  }

  private getLang(): string {
    return this.route.snapshot.paramMap.get('lang') || 'fr';
  }

  goBack(): void {
    this.router.navigate(['/', this.getLang(), 'events']);
  }

  // Getters pour le template
  getLanguageLabel(lang: Language): string {
    const translationKey = `languages.${lang.code}`;
    const translated = this.i18n.t(translationKey);
    if (translated && translated !== translationKey) {
      return translated;
    }

    const uiLang = this.langService.current;
    const fallback =
      uiLang === 'fr' ? lang.label_fr :
      uiLang === 'en' ? lang.label_en :
      lang.label_nl;

    return fallback || lang.label_fr || lang.label_en || lang.label_nl || lang.code.toUpperCase();
  }

  get selectedLanguageName(): string {
    const langId = this.eventForm.get('language')?.value;
    if (!langId) return '';
    const numericId = typeof langId === 'string' ? parseInt(langId, 10) : langId;
    const lang = this.languages().find(l => l.id === numericId);
    return lang ? this.getLanguageLabel(lang) : '';
  }

  get selectedPartnerName(): string {
    const partner = this.selectedPartner();
    return partner ? partner.name : '';
  }

  get selectedLanguageValue(): string | undefined {
    const langId = this.eventForm.get('language')?.value;
    return langId ? langId.toString() : undefined;
  }

  get selectedDifficultyValue(): string | undefined {
    return this.eventForm.get('difficulty')?.value || undefined;
  }

  get selectedGameTypeValue(): string | undefined {
    return this.eventForm.get('gameType')?.value || undefined;
  }

  // ============================================================================
  // ÉTAPE 3: Sélecteur de dates et créneaux
  // ============================================================================

  /**
   * Génère les 7 jours disponibles (J+1 à J+7)
   */
  private generateAvailableDays(): void {
    const days: DaySlot[] = [];
    const now = new Date();

    for (let i = 1; i <= 7; i++) {
      const date = new Date(now);
      date.setDate(now.getDate() + i);
      date.setHours(0, 0, 0, 0);

      days.push({
        date: date,
        formattedDate: this.formatDayDate(date),
        isTomorrow: i === 1,
        dateString: this.formatDateForBackend(date)
      });
    }

    this.availableDays.set(days);
  }

  /**
   * Génère les créneaux horaires disponibles (12h à 21h)
   */
  private generateTimeSlots(): void {
    const slots: string[] = [];
    // Créneaux de 12h à 21h (dernier créneau = 21h-22h)
    for (let hour = 12; hour <= 21; hour++) {
      const timeString = `${hour.toString().padStart(2, '0')}:00`;
      slots.push(timeString);
    }
    this.availableTimeSlots = slots;
  }

  /**
   * Formate une date au format "Mardi 5 Novembre"
   */
  private formatDayDate(date: Date): string {
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      day: 'numeric',
      month: 'long'
    };
    // Use current language from LangService
    const currentLang = this.langService.current;
    const locale = currentLang === 'fr' ? 'fr-FR' : currentLang === 'nl' ? 'nl-NL' : 'en-GB';
    const formatted = date.toLocaleDateString(locale, options);
    // Capitaliser le premier caractère
    return formatted.charAt(0).toUpperCase() + formatted.slice(1);
  }

  /**
   * Formate une date au format YYYY-MM-DD pour le backend
   */
  private formatDateForBackend(date: Date): string {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /**
   * Vérifie si un créneau est disponible (préavis de 3h)
   */
  isTimeSlotAvailable(day: DaySlot, timeSlot: string): boolean {
    const now = new Date();
    const [hours, minutes] = timeSlot.split(':').map(Number);

    const slotDateTime = new Date(day.date);
    slotDateTime.setHours(hours, minutes, 0, 0);

    // Calculer la différence en heures
    const diffInHours = (slotDateTime.getTime() - now.getTime()) / (1000 * 60 * 60);

    // Le créneau est disponible si la différence est >= 3h
    return diffInHours >= 3;
  }

  /**
   * Sélectionne un jour
   */
  selectDay(day: DaySlot): void {
    this.selectedDay.set(day);
    this.selectedTimeSlot.set(null); // Reset time slot
    this.eventForm.patchValue({ date: day.dateString, time: '' });
  }

  /**
   * Sélectionne un créneau horaire
   */
  selectTimeSlot(day: DaySlot, timeSlot: string): void {
    if (!this.isTimeSlotAvailable(day, timeSlot)) {
      return; // Ne rien faire si le créneau n'est pas disponible
    }

    this.selectedDay.set(day);
    this.selectedTimeSlot.set(timeSlot);
    this.eventForm.patchValue({
      date: day.dateString,
      time: timeSlot
    });
  }

  /**
   * Vérifie si un créneau est sélectionné
   */
  isTimeSlotSelected(day: DaySlot, timeSlot: string): boolean {
    return this.selectedDay()?.dateString === day.dateString &&
           this.selectedTimeSlot() === timeSlot;
  }
}

// ============================================================================
// INTERFACES
// ============================================================================

interface DaySlot {
  date: Date;
  formattedDate: string;
  isTomorrow: boolean;
  dateString: string; // Format YYYY-MM-DD
}




