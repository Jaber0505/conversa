import { Component, output, signal, effect, input, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { ButtonComponent, InputComponent, SelectComponent, MultiSelectComponent, FormFieldComponent } from '@shared';
import { I18nService, LangService } from '@core/i18n';
import { toSignal } from '@angular/core/rxjs-interop';

export interface EventFilters {
  searchQuery: string;
  languages: string[];
  difficulty: string | null;
  dateFrom: string | null;
  dateTo: string | null;
  priceType: 'all' | 'free' | 'paid';
  availability: 'all' | 'available' | 'almost_full';
}

export interface LanguageOption {
  value: string;
  label: string;
}

@Component({
  selector: 'app-event-filters',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TPipe,
    ButtonComponent,
    InputComponent,
    SelectComponent,
    MultiSelectComponent,
    FormFieldComponent
  ],
  templateUrl: './event-filters.component.html',
  styleUrls: ['./event-filters.component.scss']
})
export class EventFiltersComponent {
  languageOptions = input<LanguageOption[]>([]);

  filtersChanged = output<EventFilters>();

  showAdvancedFilters = signal(false);
  private readonly i18n = inject(I18nService);
  private readonly lang = inject(LangService);
  private readonly langSignal = toSignal(this.lang.lang$, { initialValue: this.lang.current });

  // Filtres
  searchQuery = signal('');
  selectedLanguages = signal<string[]>([]);
  selectedDifficulty = signal<string | null>(null);
  dateFrom = signal<string | null>(null);
  dateTo = signal<string | null>(null);
  priceType = signal<'all' | 'free' | 'paid'>('all');
  availability = signal<'all' | 'available' | 'almost_full'>('all');

  difficultyOptions = computed(() => {
    this.langSignal();
    return [
      { value: 'beginner', label: this.i18n.t('events.filters.difficulty.beginner') },
      { value: 'intermediate', label: this.i18n.t('events.filters.difficulty.intermediate') },
      { value: 'advanced', label: this.i18n.t('events.filters.difficulty.advanced') }
    ];
  });

  priceOptions = computed(() => {
    this.langSignal();
    return [
      { value: 'all', label: this.i18n.t('events.filters.price.all') },
      { value: 'free', label: this.i18n.t('events.filters.price.free') },
      { value: 'paid', label: this.i18n.t('events.filters.price.paid') }
    ];
  });

  availabilityOptions = computed(() => {
    this.langSignal();
    return [
      { value: 'all', label: this.i18n.t('events.filters.availability.all') },
      { value: 'available', label: this.i18n.t('events.filters.availability.available') },
      { value: 'almost_full', label: this.i18n.t('events.filters.availability.almost_full') }
    ];
  });

  constructor() {
    // Ã‰mettre les filtres Ã  chaque changement
    effect(() => {
      this.emitFilters();
    });
  }

  toggleAdvancedFilters(): void {
    this.showAdvancedFilters.update(v => !v);
  }

  onSearchQueryChange(value: string): void {
    this.searchQuery.set(value);
  }

  onLanguagesChange(languages: string[]): void {
    this.selectedLanguages.set(languages);
  }

  onDifficultyChange(difficulty: string | undefined): void {
    this.selectedDifficulty.set(difficulty || null);
  }

  onDateFromChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.dateFrom.set(input.value || null);
  }

  onDateToChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.dateTo.set(input.value || null);
  }

  onPriceTypeChange(value: string | undefined): void {
    this.priceType.set((value as 'all' | 'free' | 'paid') || 'all');
  }

  onAvailabilityChange(value: string | undefined): void {
    this.availability.set((value as 'all' | 'available' | 'almost_full') || 'all');
  }

  resetFilters(): void {
    this.searchQuery.set('');
    this.selectedLanguages.set([]);
    this.selectedDifficulty.set(null);
    this.dateFrom.set(null);
    this.dateTo.set(null);
    this.priceType.set('all');
    this.availability.set('all');
  }

  hasActiveFilters(): boolean {
    return (
      this.searchQuery().trim() !== '' ||
      this.selectedLanguages().length > 0 ||
      this.selectedDifficulty() !== null ||
      this.dateFrom() !== null ||
      this.dateTo() !== null ||
      this.priceType() !== 'all' ||
      this.availability() !== 'all'
    );
  }

  private emitFilters(): void {
    this.filtersChanged.emit({
      searchQuery: this.searchQuery(),
      languages: this.selectedLanguages(),
      difficulty: this.selectedDifficulty(),
      dateFrom: this.dateFrom(),
      dateTo: this.dateTo(),
      priceType: this.priceType(),
      availability: this.availability()
    });
  }
}

