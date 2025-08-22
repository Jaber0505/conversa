import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import {
  ContainerComponent as SharedContainer,
  CardComponent as SharedCard,
  BadgeComponent as SharedBadge,
  ButtonComponent as SharedButton,
} from '@shared';
import {TPipe} from "@core/i18n";

@Component({
  standalone: true,
  selector: 'app-stripe-success',
  imports: [
    CommonModule,
    SharedContainer, SharedCard, SharedBadge, SharedButton, TPipe
  ],
  templateUrl: './stripe-success.html',
  styleUrls: ['./stripe-success.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class StripeSuccessPage {
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  lang = this.route.snapshot.paramMap.get('lang') ?? 'fr';

  sessionId = this.route.snapshot.queryParamMap.get('session_id')    // format Stripe standard
    ?? this.route.snapshot.queryParamMap.get('cs');           // fallback si tu utilises ?cs=
  bookingPublicId = this.route.snapshot.queryParamMap.get('b');      // id public de réservation (optionnel)

  goToEvents() {
    this.router.navigate(['/', this.lang, 'events']);
  }
  goToMyBookings() {
    this.router.navigate(['/', this.lang, 'bookings']);
  }
  goToBooking() {
    if (this.bookingPublicId) {
      this.router.navigate(['/', this.lang, 'bookings', this.bookingPublicId]);
    }
  }
}
