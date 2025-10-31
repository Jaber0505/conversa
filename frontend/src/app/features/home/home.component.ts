import {Component, inject, signal, OnInit} from '@angular/core';
import { CommonModule } from '@angular/common';
import { SHARED_IMPORTS } from '@shared';
import { type FilterConfig } from '@shared/forms/search-bar/search-bar.component';
import {TPipe} from '@core/i18n';
import {ActivatedRoute, Router} from "@angular/router";
import {SelectOption} from "@shared/forms/select/select.component";
import {langToOptionsSS, Language} from "@core/models";
import {LanguagesApiService, AuthTokenService} from "@core/http";
import {take} from "rxjs/operators";
import {GeolocationService, NearbyStats} from "@app/core/services/geolocation.service";
import {TestimonialCardComponent} from "@shared/content/testimonial-card/testimonial-card.component";
import {AnimateOnScrollDirective} from "@shared/directives/animations/animate-on-scroll.directive";
import { EventCardComponent, type EventVM } from "@shared/content/event-card/event-card.component";

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

interface Testimonial {
  name: string;
  role: string;
  language: string;
  quote: string;
  rating: number;
  avatar: string;
}

@Component({
  standalone: true,
  selector: 'app-home',
  imports: [
    CommonModule,
    ...SHARED_IMPORTS,
    TPipe,
    TestimonialCardComponent,
    AnimateOnScrollDirective,
    EventCardComponent
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent implements OnInit {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private geolocationService = inject(GeolocationService);
  private authTokenService = inject(AuthTokenService);
  lang = this.route.snapshot.paramMap.get('lang') ?? 'fr';
  events: EventItem[] = [];
  private languagesApiService = inject(LanguagesApiService);
  allLanguage: Language[] = [];
  searchInput = "";
  selectedLangCodes : string[]=[];
  filters: FilterConfig[] = [];
  langOptions = signal<SelectOption[]>([]);
  uiLang: string | null = 'fr';
  // Prefs
  private readPrefs(): string[] {
    try { return JSON.parse(localStorage.getItem('app.prefLangs')||'[]') as string[]; } catch { return []; }
  }

  // Geolocation data
  nearbyStats = signal<NearbyStats | null>(null);
  isLoadingLocation = signal<boolean>(true);

  // Testimonials data (avatars removed to avoid 404)
  testimonials: Testimonial[] = [
    {
      name: 'Sophie Martin',
      role: 'Étudiante',
      language: 'Anglais',
      quote: 'J\'ai rencontré des personnes incroyables et mon anglais s\'est vraiment amélioré grâce aux conversations régulières.',
      rating: 5,
      avatar: '' // Placeholder will be used
    },
    {
      name: 'Thomas Dubois',
      role: 'Développeur',
      language: 'Espagnol',
      quote: 'Conversa m\'a permis de pratiquer l\'espagnol dans un cadre détendu et convivial. Je recommande vivement !',
      rating: 5,
      avatar: '' // Placeholder will be used
    },
    {
      name: 'Marie Laurent',
      role: 'Enseignante',
      language: 'Allemand',
      quote: 'Une plateforme géniale pour rencontrer des locuteurs natifs et découvrir de nouvelles cultures.',
      rating: 5,
      avatar: '' // Placeholder will be used
    }
  ];

  // Featured events (top 3)
  featured: EventVM[] = [];

  onCodesChange(codes: string[]) {
    this.selectedLangCodes = codes;
  }

  constructor() {
    this.languagesApiService.list().pipe(take(1)).subscribe((paginatedLanguage =>{
      this.allLanguage = paginatedLanguage.results;
      this.langOptions.set(langToOptionsSS(this.allLanguage, this.uiLang!));
    }))
    // prefill preferred languages
    const prefs = this.readPrefs();
    if (prefs.length) this.selectedLangCodes = prefs;
  }

  ngOnInit(): void {
    // Load nearby stats based on geolocation
    this.geolocationService.getLocationWithStats()
      .pipe(take(1))
      .subscribe({
        next: (stats) => {
          this.nearbyStats.set(stats);
          this.isLoadingLocation.set(false);
        },
        error: () => {
          // Fallback to Paris if geolocation fails
          this.nearbyStats.set({
            city: 'Paris',
            activeMembers: 42,
            upcomingEvents: 8,
            languages: ['Anglais', 'Espagnol', 'Allemand']
          });
          this.isLoadingLocation.set(false);
        }
      });

    // Featured events - Use mock data only (no API call to avoid 401 errors)
    this.featured = [
      {
        title: 'Café Polyglotte - Bruxelles Centre',
        meta: 'Mer. 30 oct., 19:00 · Le Central Café',
        desc: 'Rencontre multilingue dans une ambiance détendue',
        cta: 'Détails'
      },
      {
        title: 'Apéro Langues - Ixelles',
        meta: 'Ven. 01 nov., 18:30 · Bar Le Corbeau',
        desc: 'Pratiquez vos langues autour d\'un verre',
        cta: 'Détails'
      },
      {
        title: 'Language Exchange - Brunch',
        meta: 'Dim. 03 nov., 11:00 · Café Belga',
        desc: 'Échange linguistique convivial le dimanche',
        cta: 'Détails'
      }
    ];
  }

  onSearch(evt: { searchInput: string; selectedLangCodes: string[] }) {
    this.router.navigate(['/', this.lang, 'events'], {
      queryParams: {
        search: evt.searchInput || null,
        langs: evt.selectedLangCodes?.length ? evt.selectedLangCodes.join(',') : null
      },
      queryParamsHandling: 'merge'
    });
  }

  goToEvents()     {
    // Redirect to register if not authenticated
    if (!this.authTokenService.hasAccess()) {
      this.router.navigate(['/', this.lang, 'auth', 'register']);
      return;
    }
    this.router.navigate(['/', this.lang, 'events']);
  }

  goToSignUp()     {
    this.router.navigate(['/', this.lang, 'auth', 'register']);
  }

}
