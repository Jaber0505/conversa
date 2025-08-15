import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonComponent } from '@shared/ui/button/button.component';

@Component({
  selector: 'shared-headline-bar',
  standalone: true,
  imports: [CommonModule, ButtonComponent],
  templateUrl: './headline-bar.component.html',
  styleUrls: ['./headline-bar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HeadlineBarComponent {
  @Input() title = '';           // texte projeté possible si tu préfères
  @Input() actionLabel = '';     // i18n dans parent
  @Input() actionLink?: string;  // si fourni, <a>; sinon bouton
  @Output() action = new EventEmitter<void>();
}
