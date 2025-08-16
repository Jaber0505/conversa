import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SHARED_IMPORTS } from '@shared';
import { SearchBarComponent, type FilterConfig, type GenericSearch } from '@shared/forms/search-bar/search-bar.component';

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
  imports: [CommonModule, ...SHARED_IMPORTS, SearchBarComponent],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent {
  // Filtres génériques (N filtres)
  filters: FilterConfig[] = [
    {
      key: 'lang',
      label: 'Langue',
      type: 'select',
      options: [
        { value: 'fr', label: 'Français' },
        { value: 'en', label: 'English' },
        { value: 'es', label: 'Español' },
      ],
      searchable: true,
      placeholder: 'Toutes les langues',
    },
    {
      key: 'area',
      label: 'Zone',
      type: 'select',
      options: [
        { value: 'brussels', label: 'Bruxelles' },
        { value: 'paris',    label: 'Paris' },
        { value: 'liege',    label: 'Liège' },
      ],
      searchable: false,
      placeholder: 'Toutes les zones',
    },
    {
      key: 'free',
      label: 'Gratuit',
      type: 'boolean',
      placeholder: 'Oui / Non',
    },
  ];

  // Données brutes de test
  private readonly eventsAll: EventItem[] = [
    {
      id: 1,
      badge: { text: 'FR', variant: 'secondary' as const },
      meta: 'Jeu 19:00 • Bruxelles',
      title: 'Café linguistique — débutants',
      desc: 'Jeu “Icebreaker” • 6 places',
      lang: 'fr', area: 'brussels', free: false, cta: 'Détails',
    },
    {
      id: 2,
      badge: { text: 'EN', variant: 'tertiary' as const },
      meta: 'Ven 18:30 • Ixelles',
      title: 'Afterwork — English talk',
      desc: 'Jeu “Speed rounds” • 4 places',
      lang: 'en', area: 'brussels', free: true, cta: 'Détails',
    },
    {
      id: 3,
      badge: { text: 'ES', variant: 'secondary' as const },
      meta: 'Sam 17:00 • Saint-Gilles',
      title: 'Conversa Café — Español',
      desc: 'Jeu “Story cards” • 3 places',
      lang: 'es', area: 'brussels', free: false, cta: 'Détails',
    },
    {
      id: 4,
      badge: { text: 'FR', variant: 'secondary' as const },
      meta: 'Mer 20:00 • Paris 11e',
      title: 'Apéro-conversa — tous niveaux',
      desc: 'Ambiance chill',
      lang: 'fr', area: 'paris', free: true, cta: 'Détails',
    },
    {
      id: 5,
      badge: { text: 'EN', variant: 'tertiary' as const },
      meta: 'Mar 18:00 • Liège',
      title: 'English meetup — intermediate',
      desc: 'Jeu “Topic cards” • 5 places',
      lang: 'en', area: 'liege', free: false, cta: 'Détails',
    },
  ];

  events: EventItem[] = [...this.eventsAll];

  private norm(s?: string): string {
    return (s ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  // Réception payload SearchBar générique
  onSearch({ q, filters }: GenericSearch) {
    const nq = this.norm(q);
    const wantLang = (filters['lang'] as string | undefined) || undefined;
    const wantArea = (filters['area'] as string | undefined) || undefined;
    const wantFree = typeof filters['free'] === 'boolean' ? (filters['free'] as boolean) : undefined;

    this.events = this.eventsAll.filter(e => {
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

  onEventClick(e: EventItem) {
    console.log('Event click', e);
  }
  goToEvents()      { console.log('Naviguer vers événements'); }
  goToSignUp()      { console.log('Naviguer vers inscription'); }
  goToCategories()  { console.log('Naviguer vers catégories'); }
}
