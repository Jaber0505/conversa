import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ButtonComponent } from '@shared/ui/button/button.component';

@Component({
  selector: 'shared-headline-bar',
  standalone: true,
  imports: [CommonModule, RouterModule, ButtonComponent],
  templateUrl: './headline-bar.component.html',
  styleUrls: ['./headline-bar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HeadlineBarComponent {
  @Input() title = '';
  @Input() subtitle?: string;
  @Input() align: 'start' | 'center' = 'start';
  @Input() actionLabel = '';
  @Input() actionLink?: string | any[];
  @Output() action = new EventEmitter<void>();
}
