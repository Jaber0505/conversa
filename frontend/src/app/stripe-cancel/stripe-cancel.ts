// src/app/stripe/stripe-cancel.page.ts
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import {
  ContainerComponent as SharedContainer,
  CardComponent as SharedCard,
  BadgeComponent as SharedBadge,
  ButtonComponent as SharedButton,
} from '@shared';
import {take} from "rxjs/operators";
import {PaymentsApiService} from "@core/http";
import {TPipe} from "@core/i18n";

@Component({
  standalone: true,
  selector: 'app-stripe-cancel',
  imports: [
    CommonModule,
    SharedContainer, SharedCard, SharedBadge, SharedButton, TPipe
  ],
  templateUrl: './stripe-cancel.html',
  styleUrls: ['./stripe-cancel.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class StripeCancelPage {
  private route = inject(ActivatedRoute);
  private paymentsApiService = inject(PaymentsApiService);
  private router = inject(Router);

  lang = this.route.snapshot.paramMap.get('lang') ?? 'fr';
  bookingPublicId = this.route.snapshot.queryParamMap.get('b');     // ex: booking public id
  checkoutSessionId = this.route.snapshot.queryParamMap.get('cs');  // ex: cs_test_***

  goToEvents() {
    this.router.navigate(['/', this.lang, 'events']);
  }
  performPurchase() {
        this.paymentsApiService.createCheckoutSession({
          booking_public_id: this.bookingPublicId!,
          lang: this.lang,
        }).pipe(take(1)).subscribe({
          next: (res) => {
            window.location.href = res.url; },
          error: (err) => {
            console.error('Erreur paiement', err);
          },
        });
  }
  goToBooking() {
    if (this.bookingPublicId) {
      this.router.navigate(['/', this.lang, 'bookings']);
    }
  }
}
