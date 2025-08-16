import { Routes } from '@angular/router';
import { HomeComponent } from './features/home/home.component';
import { guestGuard } from '@core/http';

// ⬇️ i18n guard via barrel
import { languageUrlGuard } from '@core/i18n';
import {FaqComponent} from "@shared/components/faq/faq";
import {About} from "@shared/components/about/about";
import {RegisterPageComponent} from "@app/upload/register-page/register-page";

export const routes: Routes = [
  { path: '', redirectTo: '/fr', pathMatch: 'full' },
  {
    path: ':lang',
    canMatch: [languageUrlGuard],
    children: [
      { path: '', component: HomeComponent },

      // --- Maquette design, accessible seulement via URL ---
      {
        path: 'mock/mockshared',
        loadComponent: () =>
          import('./features/mock/mock-shared')
            .then(m => m.MockSharedDemo),
        data: { hidden: true }
      },

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
      { path: 'faq', component: FaqComponent },
      { path: 'about', component: About },
      { path: 'register', component: RegisterPageComponent },

      { path: '**', redirectTo: '' },
    ],
  },
  { path: '**', redirectTo: '/fr' },
];
