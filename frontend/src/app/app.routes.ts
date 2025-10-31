import {FaqComponent} from "@shared/components/faq/faq";
import {About} from "@shared/components/about/about";
import {guestGuard} from "@core/http";
import {languageUrlGuard} from "@core/i18n";
import {Routes} from "@angular/router";
import {HomeComponent} from "@app/features/home/home.component";
import {StripeSuccessPage} from "@app/stripe-success/stripe-success";
import {StripeCancelPage} from "@app/stripe-cancel/stripe-cancel";

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

      {
        path: 'events',
        loadComponent: () => import('./features/events/list/events-list.component').then(m => m.EventsListComponent)
      },

      {
        path: 'auth',
        canActivate: [guestGuard],
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'login' },
          {
            path: 'login',
            loadComponent: () => import('./features/auth/login/login.component').then(m => m.AuthLoginComponent)
          },
          {
            path: 'register',
            loadComponent: () => import('./features/auth/register/register.component').then(m => m.AuthRegisterComponent)
          },
          { path: '**', redirectTo: 'login' },
        ],
      },
      {
        path: 'register',
        loadComponent: () => import('./features/auth/register/register.component').then(m => m.AuthRegisterComponent)
      },
      {
        path: 'login',
        loadComponent: () => import('./features/auth/login/login.component').then(m => m.AuthLoginComponent)
      },
      {
        path: 'bookings',
        loadComponent: () => import('./features/bookings/my-bookings/my-bookings.component').then(m => m.MyBookingsComponent)
      },
      { path: 'faq', component: FaqComponent },
      { path: 'about', component: About },
      { path: 'stripe/success', component: StripeSuccessPage },
      { path: 'stripe/cancel',  component: StripeCancelPage  },
      { path: '**', redirectTo: '' },
    ],
  },

  { path: '**', redirectTo: '/fr' },
];
