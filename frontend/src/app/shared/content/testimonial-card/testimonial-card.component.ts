import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardComponent } from '../../ui/card/card.component';
import { BadgeComponent } from '../../ui/badge/badge.component';

@Component({
  selector: 'shared-testimonial-card',
  standalone: true,
  imports: [CommonModule, CardComponent, BadgeComponent],
  templateUrl: './testimonial-card.component.html',
  styleUrls: ['./testimonial-card.component.scss']
})
export class TestimonialCardComponent {
  @Input() name = '';
  @Input() role = '';
  @Input() language = '';
  @Input() quote = '';
  @Input() avatar = '';
  @Input() rating = 5;
}
