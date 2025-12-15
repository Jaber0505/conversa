import {FaqComponent} from "@shared/components/faq/faq";
import {About} from "@shared/components/about/about";
import {authGuard, guestGuard, adminGuard} from "@core/http";
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
        path: 'admin/audit',
        canActivate: [authGuard, adminGuard],
        loadComponent: () => import('./features/admin/audit-logs/audit-logs.component').then(m => m.AuditLogsComponent)
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
            path: 'create',
            loadComponent: () => import('./features/events/create/create.component').then(m => m.CreateEventComponent)
          },
          {
            path: ':id',
            loadComponent: () => import('./features/events/detail/detail').then(m => m.EventDetailComponent)
          }
        ]
      },

      {
        path: 'games/:id',
        canActivate: [authGuard],
        loadComponent: () => import('./features/games/games.component').then(m => m.GamesComponent)
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
      {
        path: 'profile',
        canActivate: [authGuard],
        loadComponent: () => import('./features/profile/profile.component').then(m => m.ProfileComponent)
      },
      { path: 'faq', component: FaqComponent },
      { path: 'about', component: About },
      {
        path: 'privacy-policy',
        loadComponent: () => import('./features/legal/privacy-policy/privacy-policy.component').then(m => m.PrivacyPolicyComponent)
      },
      {
        path: 'terms-of-service',
        loadComponent: () => import('./features/legal/terms-of-service/terms-of-service.component').then(m => m.TermsOfServiceComponent)
      },
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
