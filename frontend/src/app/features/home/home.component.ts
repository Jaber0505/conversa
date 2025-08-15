import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

// ⬇️ i18n via barrel
import { TPipe, TAttrDirective, I18nService, LangService, formatDateIntl, Lang } from '@i18n';

import { EventsApiService, EventDto } from '@app/features/events/events-api.service';

type EventCardVM = { id:number; badge:string; title:string; meta:string; desc:string; };

@Component({
  standalone: true,
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
  imports: [CommonModule, RouterLink, TPipe, TAttrDirective]
})
export class HomeComponent implements OnInit {
  private readonly api = inject(EventsApiService);
  private readonly i18n = inject(I18nService);
  private readonly langSvc = inject(LangService);

  readonly current = signal<Lang>(this.langSvc.current as Lang);
  events: EventCardVM[] = [];

    ngOnInit(): void {
        this.api.list().subscribe((items) => {
            const L = this.langSvc.current;

            this.events = items.map((e: EventDto) => {
                const languageLabel = this.i18n.t(`home.search.lang.${e.language}`);
                const areaLabel     = this.i18n.t(`home.search.area.${e.area}`);

                const weekday = formatDateIntl(e.start_at, L, { weekday: 'short' });
                const time    = formatDateIntl(e.start_at, L, { hour: '2-digit', minute: '2-digit' });

                const gameLabel = ({
                    speed_phrases: 'Speed Phrases',
                    topics_mix: 'Topics Mix',
                    role_cards: 'Role Cards'
                } as const)[e.game];

                return {
                    id: e.id,
                    badge: this.badgeFromLang(languageLabel),
                    title: this.i18n.t('home.event.card_title', { language: languageLabel, venue: e.venue_name }),
                    meta:  this.i18n.t('home.event.card_meta',  { weekday, time, area: areaLabel }),
                    desc:  this.i18n.t('home.event.card_desc',  { game: gameLabel, seats: e.seats_left })
                };
            });
        });
    }

    private badgeFromLang(languageLabel: string): string {
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