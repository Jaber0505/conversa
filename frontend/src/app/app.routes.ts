import { Routes } from '@angular/router';
import { HomeComponent } from './features/home/home.component';
import { guestGuard } from '@core/http';
import { languageUrlGuard } from '@core/i18n';

import { FaqComponent } from '@shared/components/faq/faq';
import { About } from '@shared/components/about/about';
import { RegisterPageComponent } from '@app/upload/register-page/register-page';

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
        path: 'auth',
        canActivate: [guestGuard],
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'register' },
          { path: 'register', component: RegisterPageComponent },
          // { path: 'login', loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent) },
          { path: '**', redirectTo: 'register' },
        ],
      },

      { path: 'faq', component: FaqComponent },
      { path: 'about', component: About },

      { path: '**', redirectTo: '' },
    ],
  },

  { path: '**', redirectTo: '/fr' },
];
