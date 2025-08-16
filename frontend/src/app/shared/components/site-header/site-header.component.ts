import { ChangeDetectionStrategy, Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, UrlSegment, UrlSegmentGroup } from '@angular/router';
import { SHARED_IMPORTS } from '@shared';
import { LanguagePopoverComponent, Lang } from '../language-popover/language-popover.component';

@Component({
  selector: 'app-site-header',
  standalone: true,
  imports: [CommonModule, RouterLink, ...SHARED_IMPORTS, LanguagePopoverComponent],
  templateUrl: './site-header.component.html',
  styleUrls: ['./site-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SiteHeaderComponent {
  private router = inject(Router);

  showLang = signal(false);
  currentLang = signal<Lang>('FR');
  langs: Lang[] = ['FR', 'EN', 'NL'];

  private readonly labels: Record<Lang, string> = { FR: 'Français', EN: 'English', NL: 'Nederlands' };
  private readonly CODE: Record<Lang, 'fr' | 'en' | 'nl'> = { FR: 'fr', EN: 'en', NL: 'nl' };
  private readonly CODES = new Set(['fr', 'en', 'nl'] as const);

  // Langue déduite de l’URL (source de vérité pour routerLink)
  langCode = computed<'fr'|'en'|'nl'>(() => {
    const tree = this.router.parseUrl(this.router.url);
    const primary = tree.root.children['primary'];
    const seg0 = primary?.segments?.[0]?.path ?? '';
    return (this.CODES.has(seg0 as any) ? (seg0 as 'fr'|'en'|'nl') : 'fr');
  });

  langText() { return this.labels[this.currentLang()]; }

  openLang()  { this.showLang.set(true); }
  closeLang() { this.showLang.set(false); }

  confirmLang(lang: Lang) {
    this.currentLang.set(lang);
    this.showLang.set(false);
    this.switchUrlLang(this.CODE[lang]);
  }

  /** Remplace (ou préfixe) /:lang dans l’URL courante (conserve path + query + hash) */
  private switchUrlLang(code: 'fr'|'en'|'nl') {
    const tree = this.router.parseUrl(this.router.url);
    const primary = tree.root.children['primary'];
    const segments = primary?.segments ?? [];

    if (segments.length && this.CODES.has(segments[0].path as any)) {
      segments[0] = new UrlSegment(code, {});
    } else {
      segments.unshift(new UrlSegment(code, {}));
    }

    tree.root.children['primary'] = new UrlSegmentGroup(segments, {});
    this.router.navigateByUrl(tree, { replaceUrl: true });
  }
}
