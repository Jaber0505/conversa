import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';

@Component({
  selector: 'shared-minimal-footer',
  standalone: true,
  imports: [CommonModule, TPipe],
  templateUrl: './minimal-footer.component.html',
  styleUrls: ['./minimal-footer.component.scss']
})
export class MinimalFooterComponent {
  readonly year = new Date().getFullYear();
}

