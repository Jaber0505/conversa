import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { ContainerComponent, CardComponent, ButtonComponent } from '@shared';

@Component({
  selector: 'app-confirm-purchase',
  standalone: true,
  imports: [CommonModule, TPipe, CardComponent, ButtonComponent],
  templateUrl: './confirm-purchase.html',
  styleUrls: ['./confirm-purchase.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfirmPurchaseComponent {
  @Input() titleKey = 'checkout.confirm.title';
  @Input() messageKey = 'checkout.confirm.message';
  @Input() cancelKey = 'common.cancel';
  @Input() buyKey = 'checkout.buy';

  @Input() priceCents?: number;

  @Input() loading = false;
  @Input() disabled = false;

  @Input() asModal = false;

  @Output() cancel = new EventEmitter<void>();
  @Output() buy = new EventEmitter<void>();

  onCancel() {
    if (!this.loading) this.cancel.emit();
  }

  onBuy() {
    if (!this.loading && !this.disabled) this.buy.emit();
  }

  price(): string | null {
    if (this.priceCents == null) return null;
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' })
      .format(this.priceCents / 100);
  }
}
