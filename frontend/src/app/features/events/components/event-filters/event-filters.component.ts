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

  // Date constraints: aujourd'hui à aujourd'hui + 7 jours
  minDate = computed(() => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  });

  maxDate = computed(() => {
    const today = new Date();
    const maxDate = new Date(today);
    maxDate.setDate(today.getDate() + 7);
    return maxDate.toISOString().split('T')[0];
  });

  // Min date for "date to" field: either dateFrom or today
  minDateTo = computed(() => {
    const from = this.dateFrom();
    return from || this.minDate();
  });

  difficultyOptions = computed(() => {
    this.langSignal();
    return [
      { value: 'easy', label: this.i18n.t('events.difficulty.easy') },
      { value: 'medium', label: this.i18n.t('events.difficulty.medium') },
      { value: 'hard', label: this.i18n.t('events.difficulty.hard') }
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
    const newDateFrom = input.value || null;
    this.dateFrom.set(newDateFrom);

    // Si la date de fin est avant la nouvelle date de début, on la réinitialise
    if (newDateFrom && this.dateTo() && this.dateTo()! < newDateFrom) {
      this.dateTo.set(null);
    }
  }

  onDateToChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.dateTo.set(input.value || null);
  }

  resetFilters(): void {
    this.searchQuery.set('');
    this.selectedLanguages.set([]);
    this.selectedDifficulty.set(null);
    this.dateFrom.set(null);
    this.dateTo.set(null);
  }

  hasActiveFilters(): boolean {
    return (
      this.searchQuery().trim() !== '' ||
      this.selectedLanguages().length > 0 ||
      this.selectedDifficulty() !== null ||
      this.dateFrom() !== null ||
      this.dateTo() !== null
    );
  }

  private emitFilters(): void {
    this.filtersChanged.emit({
      searchQuery: this.searchQuery(),
      languages: this.selectedLanguages(),
      difficulty: this.selectedDifficulty(),
      dateFrom: this.dateFrom(),
      dateTo: this.dateTo()
    });
  }
}

