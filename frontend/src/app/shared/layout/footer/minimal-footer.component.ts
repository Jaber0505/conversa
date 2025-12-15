import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { TPipe, LangService } from '@core/i18n';

@Component({
  selector: 'shared-minimal-footer',
  standalone: true,
  imports: [CommonModule, RouterLink, TPipe],
  templateUrl: './minimal-footer.component.html',
  styleUrls: ['./minimal-footer.component.scss']
})
export class MinimalFooterComponent {
  readonly year = new Date().getFullYear();

  constructor(private langService: LangService) {}

  get lang(): string {
    return this.langService.current || 'fr';
  }
}

