import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SHARED_IMPORTS } from '@shared';
import type { FilterConfig, GenericSearch } from '@shared/forms/search-bar/search-bar.component'; // ⬅️ ajout

type SelectOption = { value: string; label: string };
type EventVM = {
  badge?: { text: string; variant?: 'primary'|'secondary'|'tertiary'|'success'|'danger'|'muted' };
  meta?: string; title: string; desc?: string; cta?: string;
};

@Component({
  selector: 'app-searchbar-demo',
  standalone: true,
  imports: [CommonModule, ...SHARED_IMPORTS],
  templateUrl: './mock-shared.html',
  styleUrls: ['./mock-shared.scss'],
})
export class MockSharedDemo  {
  // --- Données de test riches ---
  items = Array.from({ length: 12 }, (_, i) => i + 1);

  langs: SelectOption[] = [
    { value: 'fr', label: 'Français' },
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Español' },
    { value: 'de', label: 'Deutsch' },
    { value: 'it', label: 'Italiano' },
    { value: 'pt', label: 'Português' },
    { value: 'nl', label: 'Nederlands' },
    { value: 'ar', label: 'العربية' },
    { value: 'zh', label: '中文 (Mandarin)' },
    { value: 'ja', label: '日本語' },
    { value: 'ko', label: '한국어' },
    { value: 'xx', label: 'Langue avec un nom extrêmement long pour tester le truncation et la mise en page sur une seule ligne' },
  ];

  manyOptions: SelectOption[] = Array.from({ length: 100 }, (_, i) => ({
    value: `opt${i+1}`, label: `Option ${i+1}`
  }));

  areas: SelectOption[] = [
    { value: 'bru', label: 'Bruxelles' },
    { value: 'par', label: 'Paris' },
    { value: 'lie', label: 'Liège' },
    { value: 'lx',  label: 'Luxembourg' },
    { value: 'ldn', label: 'London' },
    { value: 'nyc', label: 'New York City' },
  ];
  emptyOptions: SelectOption[] = [];

  // States tests
  lang?: string = 'fr';
  area?: string;
  selectedLangs: SelectOption[] = [{ value: 'fr', label: 'Français' }];
  selectedAreas: SelectOption[] = [];
  selectedValues: string[] = ['en', 'es'];

  // Events (cards)
  events: EventVM[] = [
    { badge:{text:'FR', variant:'secondary'}, meta:'Mar 10 • 18:00 • Bruxelles', title:'Café linguistique', desc:'Pratique conviviale autour d’un café', cta:'Détails' },
    { badge:{text:'EN', variant:'tertiary'},  meta:'Mer 12 • 19:00 • Paris',     title:'Afterwork',        desc:'Rencontres pro et échanges',          cta:'Détails' },
    { badge:{text:'ES', variant:'secondary'}, meta:'Jeu 20 • 17:30 • Liège',     title:'Tertulia',         desc:'Discussion en espagnol',              cta:'Détails' },
  ];

  // ✅ Config SearchBar générique (N filtres)
  searchFilters: FilterConfig[] = [
    { key: 'lang', label: 'Langue', type: 'select', options: this.langs, searchable: true,  placeholder: 'Toutes les langues' },
    { key: 'area', label: 'Zone',   type: 'select', options: this.areas, searchable: false, placeholder: 'Toutes les zones' },
    { key: 'free', label: 'Gratuit', type: 'boolean', placeholder: 'Oui / Non' }, // 3e filtre pour demo
  ];

  // Handlers
  onClick(label: string)        { console.log('btn', label); }
  onSearch(payload: GenericSearch) { console.log('search payload', payload); }
  onEvent(e: EventVM)           { console.log('open event', e); }
  onHeadlineAction()            { console.log('headline action'); }
}
