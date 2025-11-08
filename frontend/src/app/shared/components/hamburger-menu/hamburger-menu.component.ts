import { Component, signal, output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, UrlSegmentGroup } from '@angular/router';
import { TPipe, type Lang } from '@core/i18n';
import { AuthTokenService } from '@core/http';

@Component({
  selector: 'shared-hamburger-menu',
  standalone: true,
  imports: [CommonModule, RouterModule, TPipe],
  templateUrl: './hamburger-menu.component.html',
  styleUrls: ['./hamburger-menu.component.scss']
})
export class HamburgerMenuComponent {
  // Signal for menu open/close state
  isOpen = signal(false);

  // Output event when menu state changes (for parent to handle overlay)
  menuStateChange = output<boolean>();

  // Inject auth service to check if user is logged in
  protected tokens = inject(AuthTokenService);

  constructor(private router: Router) {}

  /**
   * Toggle hamburger menu open/close state
   */
  toggleMenu(): void {
    this.isOpen.update(value => !value);
    this.menuStateChange.emit(this.isOpen());
  }

  /**
   * Close menu (used when clicking a link)
   */
  closeMenu(): void {
    this.isOpen.set(false);
    this.menuStateChange.emit(false);
  }

  /**
   * Get current language code for routing (same logic as site-header)
   */
  langCode(): Lang {
    const tree = this.router.parseUrl(this.router.url);
    const primary: UrlSegmentGroup | undefined = tree.root.children['primary'];
    const segs = primary?.segments ?? [];
    const code = segs[0]?.path as Lang | undefined;
    return (code && (['fr', 'en', 'nl'] as const).includes(code)) ? code : 'fr';
  }
}
