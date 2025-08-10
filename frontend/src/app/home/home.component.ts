import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

// i18n (chemins selon ton projet)
import { TPipe } from '@app/core/i18n/t.pipe';
import { TAttrDirective } from '@app/core/i18n/t-attr.directive';
import { I18nService } from '@app/core/i18n/i18n.service';
import { LangService } from '@app/core/i18n/lang.service';
import { formatDateIntl } from '@app/core/i18n/intl.helpers';

// Service mock (remplacé plus tard par l'API Django)
import { EventsApiService, EventDto } from '@app/features/events/events-api.service';

type EventCardVM = {
  id: number;
  badge: string;   // En / Nl / Es / Fr
  title: string;   // i18n: home.event.card_title
  meta: string;    // i18n: home.event.card_meta
  desc: string;    // i18n: home.event.card_desc
};

@Component({
  standalone: true,
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
  imports: [CommonModule, RouterLink, TPipe, TAttrDirective],
})
export class HomeComponent implements OnInit {
  private readonly api = inject(EventsApiService);
  private readonly i18n = inject(I18nService);
  private readonly lang = inject(LangService);

  events: EventCardVM[] = [];

  ngOnInit(): void {
    this.api.list().subscribe((items) => {
      const L = this.lang.current;

      this.events = items.map((e: EventDto) => {
        // Libellés via i18n (réutilise les options du filtre)
        const languageLabel = this.i18n.t(`home.search.lang.${e.language}`); // en/nl/es/fr
        const areaLabel     = this.i18n.t(`home.search.area.${e.area}`);     // center/ixelles/stg

        // Date/heure en locale courante
        const weekday = formatDateIntl(e.start_at, L, { weekday: 'short' }); // ex: mar.
        const time    = formatDateIntl(e.start_at, L, { hour: '2-digit', minute: '2-digit' });

        // Nom du jeu (simple libellé; i18n possible plus tard)
        const gameLabel = ({
          speed_phrases: 'Speed Phrases',
          topics_mix: 'Topics Mix',
          role_cards: 'Role Cards',
        } as const)[e.game];

        return {
          id: e.id,
          badge: this.badgeFromLang(languageLabel),
          title: this.i18n.t('home.event.card_title', { language: languageLabel, venue: e.venue_name }),
          meta:  this.i18n.t('home.event.card_meta',  { weekday, time, area: areaLabel }),
          desc:  this.i18n.t('home.event.card_desc',  { game: gameLabel, seats: e.seats_left }),
        };
      });
    });
  }

  private badgeFromLang(languageLabel: string): string {
    // Abréviation propre (2 lettres) avec fallback
    if (!languageLabel) return '—';
    const map: Record<string, string> = {
      Anglais: 'En', English: 'En',
      Néerlandais: 'Nl', Dutch: 'Nl',
      Espagnol: 'Es', Spanish: 'Es',
      Français: 'Fr', French: 'Fr'
    };
    return map[languageLabel] ?? languageLabel.slice(0, 2);
  }
}
