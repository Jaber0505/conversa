import {FaqComponent} from "@shared/components/faq/faq";
import {About} from "@shared/components/about/about";
import {authGuard, guestGuard} from "@core/http";
import {languageUrlGuard} from "@core/i18n";
import {homeGuard} from "@app/core/guards/home.guard";
import {Routes} from "@angular/router";
import {HomeComponent} from "@app/features/home/home.component";

export const routes: Routes = [
  { path: '', redirectTo: '/fr', pathMatch: 'full' },

  {
    path: ':lang',
    canMatch: [languageUrlGuard],
    children: [
      {
        path: '',
        component: HomeComponent,
        canActivate: [homeGuard]
      },

      {
        path: 'events',
        canActivate: [authGuard],
        children: [
          {
            path: '',
            loadComponent: () => import('./features/events/list/events-list.component').then(m => m.EventsListComponent)
          },
          {
            path: ':id',
            loadComponent: () => import('./features/events/detail/detail').then(m => m.EventDetailComponent)
          }
        ]
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
            path: 'forgot',
            loadComponent: () => import('./features/auth/forgot/forgot.component').then(m => m.ForgotPasswordComponent)
          },
          {
            path: 'register',
            loadComponent: () => import('./features/auth/register/register.component').then(m => m.AuthRegisterComponent)
          },
          { path: '**', redirectTo: 'login' },
        ],
      },
      {
        path: 'bookings',
        canActivate: [authGuard],
        loadComponent: () => import('./features/bookings/my-bookings/my-bookings.component').then(m => m.MyBookingsComponent)
      },
      { path: 'faq', component: FaqComponent },
      { path: 'about', component: About },
      {
        path: 'stripe/success',
        canActivate: [authGuard],
        loadComponent: () => import('./features/payments/success/success.component').then(m => m.PaymentSuccessComponent)
      },
      {
        path: 'stripe/cancel',
        canActivate: [authGuard],
        loadComponent: () => import('./features/payments/cancel/cancel.component').then(m => m.PaymentCancelComponent)
      },
      { path: '**', redirectTo: '' },
    ],
  },

  { path: '**', redirectTo: '/fr' },
];
