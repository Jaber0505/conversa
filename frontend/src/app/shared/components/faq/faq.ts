import { Component, ChangeDetectionStrategy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {FaqItemComponent} from "@app/shared/components/faq/component/faqItem/faq-item.component";
import {TPipe} from "@core/i18n";

type FaqItem = {
  id: string;
  group: 'getting_started' | 'events' | 'account' | 'payments';
  qKey: string;
  aKey: string;
};

@Component({
  selector: 'app-faq',
  standalone: true,
  imports: [CommonModule, FormsModule, TPipe, FaqItemComponent, TPipe],
  templateUrl: './faq.html',
  styleUrls: ['./faq.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FaqComponent {

}
