import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { LangService } from '../index';

@Component({
  selector: 'app-root-redirect',
  standalone: true,
  template: ``,
})
export class RootRedirectComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly lang = inject(LangService);

  ngOnInit(): void {
    const targetLang = this.lang.current;
    const routeExtra = this.router.getCurrentNavigation()?.extras.state as { to?: string };
    const pathSuffix = routeExtra?.to ?? '';

    const segments = ['/', targetLang];
    if (pathSuffix) segments.push(...pathSuffix.split('/'));

    this.router.navigate(segments, { replaceUrl: true });
  }
}
