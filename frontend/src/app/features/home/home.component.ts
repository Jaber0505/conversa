import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SHARED_IMPORTS } from '@shared';

type SelectOption = { value: string; label: string };
type EventVM = {
  badge?: { text: string; variant?: 'primary'|'secondary'|'tertiary'|'success'|'danger'|'muted' };
  meta?: string; title: string; desc?: string; cta?: string;
};

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ...SHARED_IMPORTS],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent {
  // Données de la recherche
  langs: SelectOption[] = [
    { value: 'fr', label: 'Français' },
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Español' },
    { value: 'de', label: 'Deutsch' },
    { value: 'nl', label: 'Nederlands' },
  ];
  areas: SelectOption[] = [
    { value: 'bru', label: 'Bruxelles' },
    { value: 'ix',  label: 'Ixelles' },
    { value: 'stg', label: 'Saint-Gilles' },
    { value: 'ctr', label: 'Centre' },
  ];

  // Catégories (cartes)
  categories = [
    { title: 'Conversa Café',  subtitle: 'Rencontres informelles' },
    { title: 'Conversa Pro',   subtitle: 'Échanges professionnels' },
    { title: 'Conversa Events', subtitle: 'Événements publics' },
  ];

  // Événements
  events: EventVM[] = [
    { badge:{text:'FR', variant:'secondary'}, meta:'Mar 10 • 18:00 • Bruxelles', title:'Café linguistique', desc:'Pratique conviviale autour d’un café', cta:'Détails' },
    { badge:{text:'EN', variant:'tertiary'},  meta:'Mer 12 • 19:00 • Paris',     title:'Afterwork',        desc:'Rencontres pro et échanges',          cta:'Détails' },
    { badge:{text:'ES', variant:'secondary'}, meta:'Jeu 20 • 17:30 • Liège',     title:'Tertulia',         desc:'Discussion en espagnol',              cta:'Détails' },
  ];

  // Actions
  onSearch(payload: { q?: string; lang?: string; area?: string }) {
    console.log('search', payload);
  }
  onHeadlineAction() { console.log('headline action'); }
  onEvent(e: EventVM) { console.log('open event', e); }
}
