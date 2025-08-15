import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardComponent } from '@shared/ui/card/card.component';
import { BadgeComponent } from '@shared/ui/badge/badge.component';
import { ButtonComponent } from '@shared/ui/button/button.component';

export interface EventVM {
  badge?: { text: string; variant?: 'primary'|'secondary'|'tertiary'|'success'|'danger'|'muted'; };
  meta?: string;    // ex: "mar 10 • 18:00 • Bruxelles"
  title: string;
  desc?: string;
  cta?: string;
}

@Component({
  selector: 'shared-event-card',
  standalone: true,
  imports: [CommonModule, CardComponent, BadgeComponent, ButtonComponent],
  templateUrl: './event-card.component.html',
  styleUrls: ['./event-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventCardComponent {
  @Input() event!: EventVM;
  @Output() cta = new EventEmitter<void>();
}
