import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { TPipe } from '@core/i18n';

@Component({
  selector: 'app-site-footer',
  standalone: true,
  imports: [CommonModule, RouterModule, TPipe],
  templateUrl: './site-footer.component.html',
  styleUrls: ['./site-footer.component.scss']
})
export class SiteFooterComponent {
  private router = inject(Router);
  currentYear = new Date().getFullYear();

  navigateToFaq() {
    this.router.navigate(['/fr/faq']);
  }

  navigateToAbout() {
    this.router.navigate(['/fr/about']);
  }
}
