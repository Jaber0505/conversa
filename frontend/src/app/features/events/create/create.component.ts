import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { take, finalize } from 'rxjs/operators';

import { TPipe } from '@core/i18n';
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
import { ConfirmPurchaseComponent } from '@app/shared/components/modals/confirm-purchase/confirm-purchase.component';

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
    ConfirmPurchaseComponent
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

  // Étapes
  currentStep = signal(1);
  totalSteps = 4;

  // Données du formulaire
  eventForm!: FormGroup;

  // Données chargées
  partners = signal<Partner[]>([]);
  languages = signal<Language[]>([]);
  filteredPartners = signal<Partner[]>([]);

  // Étape 1: Partner sélectionné
  selectedPartner = signal<Partner | null>(null);
  postalCode = '';

  // Événement créé (brouillon)
  createdEventId = signal<number | null>(null);
  createdBookingId = signal<string | null>(null);

  // Modal paiement
  showPaymentModal = signal(false);

  // Loading states
  loading = signal(false);
  error = signal<string | null>(null);

  // Options pour les selects
  languageOptions = signal<{ value: string; label: string }[]>([]);
  difficultyOptions: { value: string; label: string }[] = [
    { value: 'beginner', label: '' }, // sera traduit dans le template
    { value: 'medium', label: '' },
    { value: 'advanced', label: '' }
  ];

  ngOnInit(): void {
    this.initForm();
    this.loadLanguages();
    this.loadPartners();
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
    });
  }

  private loadLanguages(): void {
    this.languagesApi.list().pipe(take(1)).subscribe({
      next: (response) => {
        this.languages.set(response.results);

        // Créer les options pour le select
        const options = response.results.map(lang => ({
          value: lang.id.toString(),
          label: this.getLanguageLabel(lang)
        }));
        this.languageOptions.set(options);
      },
      error: (err) => {
        console.error('Error loading languages:', err);
      }
    });
  }

  private loadPartners(): void {
    this.partnersApi.list().pipe(take(1)).subscribe({
      next: (response) => {
        this.partners.set(response.results);
        this.filteredPartners.set(response.results);
      },
      error: (err) => {
        console.error('Error loading partners:', err);
      }
    });
  }

  // Étape 1: Filtrer par code postal via l'API
  onPostalCodeChange(postalCode: string): void {
    this.postalCode = postalCode.trim();

    // Charger les partners depuis l'API avec le filtre
    this.partnersApi.list(this.postalCode || undefined).pipe(take(1)).subscribe({
      next: (response) => {
        this.partners.set(response.results);
        this.filteredPartners.set(response.results);
      },
      error: (err) => {
        console.error('Error loading partners:', err);
      }
    });
  }

  selectPartner(partner: Partner): void {
    this.selectedPartner.set(partner);
    this.eventForm.patchValue({ partner: partner.id });
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

  // Étape 4: Création de l'événement
  createEvent(): void {
    if (!this.eventForm.valid) {
      this.error.set('Veuillez remplir tous les champs requis');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.loader.show('Création de votre événement...');

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
      datetime_start: datetime_start
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
        this.createdEventId.set(response.id);

        // Le backend crée automatiquement un booking pour l'organisateur
        // On doit récupérer ce booking pour pouvoir payer
        this.fetchOrganizerBooking(response.id);
      },
      error: (err) => {
        console.error('Error creating event:', err);
        this.error.set('Erreur lors de la création de l\'événement');
      }
    });
  }

  private fetchOrganizerBooking(eventId: number): void {
    // Le booking de l'organisateur est créé automatiquement par le backend
    // On le récupère via l'API bookings
    this.eventsApi.get(eventId).pipe(take(1)).subscribe({
      next: (event: any) => {
        // Pour simplifier, on affiche directement la modal de paiement
        // L'utilisateur pourra payer via la liste de ses brouillons
        this.showPaymentModal.set(true);
      },
      error: (err) => {
        console.error('Error fetching event:', err);
        // Même en cas d'erreur, on peut rediriger vers la liste
        this.showPaymentModal.set(true);
      }
    });
  }

  // Modal de paiement
  payNow(): void {
    const eventId = this.createdEventId();
    if (!eventId) return;

    this.loader.show('Redirection vers le paiement...');

    // On doit d'abord récupérer le booking de l'organisateur
    // puis créer une session de paiement
    this.eventsApi.get(eventId).pipe(take(1)).subscribe({
      next: (event: any) => {
        // Note: Le backend devrait nous retourner le booking_id de l'organisateur
        // Pour l'instant, on redirige vers la liste des événements
        // où l'utilisateur pourra payer depuis la section "Mes événements"
        this.router.navigate(['/', this.getLang(), 'events']);
      },
      error: (err) => {
        console.error('Error:', err);
        this.loader.hide();
      }
    });
  }

  payLater(): void {
    // Rediriger vers la liste des événements
    this.router.navigate(['/', this.getLang(), 'events']);
  }

  closePaymentModal(): void {
    this.showPaymentModal.set(false);
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
    const uiLang = this.getLang();
    if (uiLang === 'fr') return lang.label_fr;
    if (uiLang === 'en') return lang.label_en;
    return lang.label_nl;
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
}
