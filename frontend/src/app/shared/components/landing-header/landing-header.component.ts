import { Component, inject, OnInit, OnDestroy, HostBinding, AfterViewInit, ElementRef, Renderer2, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { ButtonComponent } from '@shared/ui/button/button.component';
import { LanguagePopoverComponent, type Lang } from '@shared/components/language-popover/language-popover.component';
import { LangService } from '@core/i18n';
import { TPipe } from '@core/i18n';
import { fromEvent, Subject } from 'rxjs';
import { takeUntil, throttleTime } from 'rxjs/operators';

@Component({
  selector: 'app-landing-header',
  standalone: true,
  imports: [CommonModule, RouterModule, ButtonComponent, TPipe, LanguagePopoverComponent],
  templateUrl: './landing-header.component.html',
  styleUrls: ['./landing-header.component.scss']
})
export class LandingHeaderComponent implements OnInit, AfterViewInit, OnDestroy {
  @Input() spacer = false; // Quand true, ajoute un espace sous le header égal à sa hauteur
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private langSvc = inject(LangService);
  private host = inject(ElementRef<HTMLElement>);
  private renderer = inject(Renderer2);
  private destroy$ = new Subject<void>();

  currentLang: Lang = (this.route.snapshot.paramMap.get('lang') as Lang) || 'fr';
  langs: ReadonlyArray<Lang> = ['fr','en','nl'];
  showLang = false;
  preferredLangs: Lang[] = (() => { try { return JSON.parse(localStorage.getItem('app.prefLangs')||'[]')} catch { return [] } })();

  @HostBinding('class.header-hidden') isHeaderHidden = false;
  private lastScrollTop = 0;

  ngOnInit() {
    // Auto-hide header on scroll
    const scrollContainer = document.querySelector('.scroll-container');
    if (scrollContainer) {
      fromEvent(scrollContainer, 'scroll')
        .pipe(
          throttleTime(100),
          takeUntil(this.destroy$)
        )
        .subscribe(() => {
          const scrollTop = scrollContainer.scrollTop;

          // Show header when scrolling up, hide when scrolling down
          if (scrollTop > this.lastScrollTop && scrollTop > 80) {
            this.isHeaderHidden = true;
          } else {
            this.isHeaderHidden = false;
          }

          this.lastScrollTop = scrollTop;
        });
    }
  }

  ngAfterViewInit(): void {
    this.updateHeaderHeight();
    fromEvent(window, 'resize')
      .pipe(throttleTime(150), takeUntil(this.destroy$))
      .subscribe(() => this.updateHeaderHeight());
  }

  private updateHeaderHeight() {
    const header: HTMLElement | null = this.host.nativeElement.querySelector('.landing-header');
    const h = header?.offsetHeight ?? 88;
    // Expose header height as CSS variable for pages needing an offset (auth, forgot)
    this.renderer.setStyle(document.documentElement, '--header-h', `${h}px`);
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  changeLang(lang: string) {
    this.router.navigate(['/', lang]);
  }

  goToLogin() {
    this.router.navigate(['/', this.currentLang, 'auth', 'login']);
  }

  goToRegister() {
    this.router.navigate(['/', this.currentLang, 'auth', 'register']);
  }

  // Lang popover handlers
  openLang() { this.showLang = true; }
  closeLang() { this.showLang = false; }
  onLangSave(next: Lang) {
    this.langSvc.set(next); // met à jour l'URL via LangService
    this.currentLang = next;
    this.closeLang();
  }
  onLangPrefsSave(prefs: Lang[]) {
    this.preferredLangs = prefs;
    try { localStorage.setItem('app.prefLangs', JSON.stringify(prefs)); } catch {}
  }
}
