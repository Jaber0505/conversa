import { Component, ChangeDetectionStrategy, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-faq-item',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './faq-item.component.html',
  styleUrls: ['./faq-item.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FaqItemComponent {
  number = input.required<number>();
  question = input.required<string>();
  answer = input.required<string>();

  open = signal(false);
  toggle() { this.open.update(v => !v); }
}
