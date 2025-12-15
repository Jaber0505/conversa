import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe, LangService } from '@core/i18n';
import { ContainerComponent } from '../../../shared/layout/container/container.component';
import { ButtonComponent } from '../../../shared/ui/button/button.component';
import { Router } from '@angular/router';

@Component({
  selector: 'app-privacy-policy',
  standalone: true,
  imports: [CommonModule, TPipe, ContainerComponent, ButtonComponent],
  templateUrl: './privacy-policy.component.html',
  styleUrls: ['./privacy-policy.component.scss']
})
export class PrivacyPolicyComponent {
  constructor(
    private router: Router,
    private langService: LangService
  ) {}

  get lang(): string {
    return this.langService.current || 'fr';
  }

  goBack(): void {
    this.router.navigate(['/', this.lang]);
  }
}
