import { Routes } from '@angular/router';
import { HomeComponent } from './features/home/home.component';
import { guestGuard } from './core/http/guards/guest.guard';

// ⬇️ i18n guard via barrel
import { languageUrlGuard } from '@i18n';

export const routes: Routes = [
  { path: '', redirectTo: '/fr', pathMatch: 'full' },
  {
    path: ':lang',
    canMatch: [languageUrlGuard],
    children: [
      { path: '', component: HomeComponent },

      {
        path: 'auth',
        // Ici, on protège les pages invitées (login/register)
        canActivate: [guestGuard],
        children: [
          // { path: 'login', loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent) },
          // { path: 'register', loadComponent: () => import('./features/auth/register/register.component').then(m => m.RegisterComponent) },
        ]
      },

      // // 🔒 Zones privées (ex : tableau de bord utilisateur)
      // {
      //   path: 'dashboard',
      //   canActivate: [authGuard],
      //   loadComponent: () => import('./features/dashboard/dashboard.component')
      //     .then(m => m.DashboardComponent),
      // },
      // {
      //   path: 'profile',
      //   canActivate: [authGuard],
      //   loadComponent: () => import('./features/profile/profile.component')
      //     .then(m => m.ProfileComponent),
      // },

      { path: '**', redirectTo: '' },
    ],
  },
  { path: '**', redirectTo: '/fr' },
];
