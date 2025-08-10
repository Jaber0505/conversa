import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { LangService } from '@app/core/i18n/lang.service';

@Component({
  selector: 'app-root-redirect',
  standalone: true,
  template: ``,
})
export class RootRedirectComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly lang = inject(LangService);

  ngOnInit(): void {
    const target = this.lang.current;
    this.router.navigate(['/', target], { replaceUrl: true });
  }
}
