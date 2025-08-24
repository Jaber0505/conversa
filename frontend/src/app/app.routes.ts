import {FaqComponent} from "@shared/components/faq/faq";
import {About} from "@shared/components/about/about";
import {LoginPageComponent} from "@app/login-page/login-page";
import {RegisterPageComponent} from "@app/upload/register-page/register-page";
import {guestGuard} from "@core/http";
import {languageUrlGuard} from "@core/i18n";
import {Routes} from "@angular/router";
import {HomeComponent} from "@app/features/home/home.component";
import {EventListMockComponent} from "@app/event-list-mock/event-list-mock";
import {StripeSuccessPage} from "@app/stripe-success/stripe-success";
import {StripeCancelPage} from "@app/stripe-cancel/stripe-cancel";
import {BookingsListComponent} from "@app/booking-page/booking-page";

export const routes: Routes = [
  { path: '', redirectTo: '/fr', pathMatch: 'full' },

  {
    path: ':lang',
    canMatch: [languageUrlGuard],
    children: [
      { path: '', component: HomeComponent },

      {
        path: 'mock/mockshared',
          loadComponent: () =>
            import('./features/mock/mock-shared').then(m => m.MockSharedDemo),
          data: { hidden: true },
      },

      { path: 'events', component: EventListMockComponent },

      {
        path: 'auth',
        canActivate: [guestGuard],
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'register' },

          { path: '**', redirectTo: 'register' },
        ],
      },
      { path: 'register', component: RegisterPageComponent },
      { path: 'login', component: LoginPageComponent },
      { path: 'bookings', component: BookingsListComponent },
      { path: 'faq', component: FaqComponent },
      { path: 'about', component: About },
      { path: 'stripe/success', component: StripeSuccessPage },
      { path: 'stripe/cancel',  component: StripeCancelPage  },
      { path: '**', redirectTo: '' },
    ],
  },

  { path: '**', redirectTo: '/fr' },
];
