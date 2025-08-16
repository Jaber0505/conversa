import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SHARED_IMPORTS } from '@shared';
import { SearchBarComponent, type FilterConfig, type GenericSearch } from '@shared/forms/search-bar/search-bar.component';
import {I18nService, TPipe} from '@core/i18n'; // ⬅️ i18n

type EventItem = {
  id: number;
  title: string;
  desc?: string;
  meta?: string;
  lang?: string;
  area?: string;
  free?: boolean;
  badge?: { text: string; variant?: 'primary'|'secondary'|'tertiary'|'success'|'danger'|'muted' };
  cta?: string;
};

@Component({
  standalone: true,
  selector: 'app-home',
  imports: [CommonModule, ...SHARED_IMPORTS, SearchBarComponent, TPipe],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent {
  private readonly i18n = inject(I18nService);

  // Données brutes de test (on garde le FR tel quel)
  private readonly eventsAll: EventItem[] = [
    { id: 1, badge: { text: 'FR', variant: 'secondary' }, meta: 'Jeu 19:00 • Bruxelles', title: 'Café linguistique — débutants', desc: 'Jeu “Icebreaker” • 6 places', lang: 'fr', area: 'brussels', free: false },
    { id: 2, badge: { text: 'EN', variant: 'tertiary' },  meta: 'Ven 18:30 • Ixelles',   title: 'Afterwork — English talk',       desc: 'Jeu “Speed rounds” • 4 places',  lang: 'en', area: 'brussels', free: true  },
    { id: 3, badge: { text: 'ES', variant: 'secondary' }, meta: 'Sam 17:00 • Saint-Gilles', title: 'Conversa Café — Español',     desc: 'Jeu “Story cards” • 3 places',  lang: 'es', area: 'brussels', free: false },
    { id: 4, badge: { text: 'FR', variant: 'secondary' }, meta: 'Mer 20:00 • Paris 11e',    title: 'Apéro-conversa — tous niveaux', desc: 'Ambiance chill',             lang: 'fr', area: 'paris',    free: true  },
    { id: 5, badge: { text: 'EN', variant: 'tertiary' },  meta: 'Mar 18:00 • Liège',        title: 'English meetup — intermediate', desc: 'Jeu “Topic cards” • 5 places', lang: 'en', area: 'liege',   free: false },
  ];

  events: EventItem[] = [];

  // Filtres i18n (reconstruits à chaque changement de langue)
  filters: FilterConfig[] = [];

  constructor() {
    this.rebuildI18n();
    // Si ton I18nService expose un signal/observable de readiness, on regénère:
    this.i18n.ready$.subscribe(() => this.rebuildI18n());
  }

  private rebuildI18n() {
    // 1) Filtres
    this.filters = [
      {
        key: 'lang',
        label: this.i18n.t('shared.filters.lang.label'),
        type: 'select',
        options: [
          { value: 'fr', label: this.i18n.t('shared.filters.lang.options.fr') },
          { value: 'en', label: this.i18n.t('shared.filters.lang.options.en') },
          { value: 'es', label: this.i18n.t('shared.filters.lang.options.es') },
        ],
        searchable: true,
        placeholder: this.i18n.t('shared.filters.lang.placeholder'),
      },
      {
        key: 'area',
        label: this.i18n.t('shared.filters.area.label'),
        type: 'select',
        options: [
          { value: 'brussels', label: this.i18n.t('shared.filters.area.options.brussels') },
          { value: 'paris',    label: this.i18n.t('shared.filters.area.options.paris') },
          { value: 'liege',    label: this.i18n.t('shared.filters.area.options.liege') },
        ],
        searchable: false,
        placeholder: this.i18n.t('shared.filters.area.placeholder'),
      },
      {
        key: 'free',
        label: this.i18n.t('shared.filters.free.label'),
        type: 'boolean',
        placeholder: this.i18n.t('shared.filters.free.placeholder'),
      },
    ];

    // 2) CTA “Détails” traduite (facultatif si utilisé par la carte)
    this.events = this.eventsAll.map(e => ({ ...e, cta: this.i18n.t('shared.actions.details') }));
  }

  private norm(s?: string): string {
    return (s ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  onSearch({ q, filters }: GenericSearch) {
    const nq = this.norm(q);
    const wantLang = (filters['lang'] as string | undefined) || undefined;
    const wantArea = (filters['area'] as string | undefined) || undefined;
    const wantFree = typeof filters['free'] === 'boolean' ? (filters['free'] as boolean) : undefined;

    this.events = this.eventsAll
      .map(e => ({ ...e, cta: this.i18n.t('shared.actions.details') }))
      .filter(e => {
        const inText =
          !nq ||
          this.norm(e.title).includes(nq) ||
          this.norm(e.desc).includes(nq) ||
          this.norm(e.meta).includes(nq);

        const inLang = !wantLang || e.lang === wantLang;
        const inArea = !wantArea || e.area === wantArea;
        const inFree = wantFree === undefined || e.free === wantFree;

        return inText && inLang && inArea && inFree;
      });
  }

  onEventClick(e: EventItem) { console.log('Event click', e); }
  goToEvents()     { console.log('Naviguer vers événements'); }
  goToSignUp()     { console.log('Naviguer vers inscription'); }
  goToCategories() { console.log('Naviguer vers catégories'); }
}
