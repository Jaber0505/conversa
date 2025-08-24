import {Component, inject, signal} from '@angular/core';
import { CommonModule } from '@angular/common';
import { SHARED_IMPORTS } from '@shared';
import { SearchBarComponent, type FilterConfig, type GenericSearch } from '@shared/forms/search-bar/search-bar.component';
import {I18nService, TPipe} from '@core/i18n';
import {BlockingSpinnerService} from "@app/core/http/services/spinner-service";
import {ActivatedRoute, Router} from "@angular/router";
import {SharedSearchPanelComponent} from "@app/shared-search-panel/shared-search-panel";
import {SelectOption} from "@shared/forms/select/select.component";
import {langToOptionsSS, Language} from "@core/models";
import {LanguagesApiService} from "@core/http";

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
  imports: [CommonModule, ...SHARED_IMPORTS, TPipe, SharedSearchPanelComponent],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent {
  private readonly i18n = inject(I18nService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  lang = this.route.snapshot.paramMap.get('lang') ?? 'fr';
  events: EventItem[] = [];
  private languagesApiService = inject(LanguagesApiService);
  allLanguage: Language[] = [];
  searchInput = "";
  selectedLangCodes : string[]=[];
  filters: FilterConfig[] = [];
  langOptions = signal<SelectOption[]>([]);
  uiLang: string | null = 'fr';
  onCodesChange(codes: string[]) {
    this.selectedLangCodes = codes;
  }

  constructor( private loader: BlockingSpinnerService) {
    this.languagesApiService.list().subscribe((paginatedLanguage =>{
      this.allLanguage = paginatedLanguage.results;
      this.langOptions.set(langToOptionsSS(this.allLanguage, this.uiLang!));
    }))
  }

  onSearch(evt: { searchInput: string; selectedLangCodes: string[] }) {
    debugger;
    this.router.navigate(['fr','events'], {
      queryParams: {
        search: evt.searchInput || null,
        langs: evt.selectedLangCodes?.length ? evt.selectedLangCodes.join(',') : null
      },
      queryParamsHandling: 'merge'
    });
  }

  goToEvents()     {
    this.router.navigate(['/', this.lang, 'events']);
    console.log('Naviguer vers événements');

  }
  goToSignUp()     {
    this.router.navigate(['/', this.lang, 'register']);
    console.log('Naviguer vers inscription'); }
}
