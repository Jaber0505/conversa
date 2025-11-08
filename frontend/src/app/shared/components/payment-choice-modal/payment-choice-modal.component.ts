import { Component, Input, Output, EventEmitter, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';

import { ModalComponent } from '@shared/ui/modal/modal.component';
import { ButtonComponent } from '@shared/ui/button/button.component';
import { TPipe } from '@core/i18n';
import { EventsApiService, PaymentsApiService } from '@core/http';

@Component({
  selector: 'app-payment-choice-modal',
  standalone: true,
  imports: [
    CommonModule,
    ModalComponent,
    ButtonComponent,
    TPipe
  ],
  templateUrl: './payment-choice-modal.component.html',
  styleUrls: ['./payment-choice-modal.component.scss']
})
export class PaymentChoiceModalComponent {
  private readonly eventsApi = inject(EventsApiService);
  private readonly paymentsApi = inject(PaymentsApiService);
  private readonly route = inject(ActivatedRoute);

  @Input() isOpen = false;
  @Input() eventId: number | null = null;
  @Input() eventPrice = 700; // prix en centimes (7.00€)

  @Output() closeModal = new EventEmitter<void>();
  @Output() paymentSuccess = new EventEmitter<void>();
  @Output() payLater = new EventEmitter<void>();

  // état du composant
  loading = signal(false);
  error = signal<string | null>(null);

  /**
   * L'utilisateur choisit de payer maintenant (organisateur)
   * Redirige vers Stripe Checkout via l'alias request-publication
   */
  onPayNow(): void {
    if (!this.eventId) {
      this.error.set('ID évènement manquant');
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    const lang = this.getLang();
    this.eventsApi.requestPublication(this.eventId, lang).subscribe({
      next: (pubResponse) => {
        if (!pubResponse || !pubResponse.url) {
          this.error.set('URL de paiement indisponible');
          this.loading.set(false);
          return;
        }
        window.location.href = pubResponse.url;
      },
      error: (err) => {
        console.error('Error requesting publication:', err);
        this.error.set(err?.error?.error || err?.error?.detail || 'Erreur lors de la préparation du paiement');
        this.loading.set(false);
      }
    });
  }

  /**
   * Récupérer la langue courante
   */
  private getLang(): string {
    return this.route.snapshot.paramMap.get('lang') || 'fr';
  }

  /**
   * L'utilisateur choisit de payer plus tard
   */
  onPayLater(): void {
    this.payLater.emit();
  }

  /**
   * Fermer le modal
   */
  close(): void {
    this.closeModal.emit();
  }

  /**
   * Formater le prix
   */
  get formattedPrice(): string {
    return (this.eventPrice / 100).toFixed(2);
  }
}
