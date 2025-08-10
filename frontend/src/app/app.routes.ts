// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { AboutComponent } from './features/about/about.component';
import { SettingsComponent } from './features/settings/settings.component';
import { languageUrlGuard } from './core/i18n/language-url.guard';
import { RootRedirectComponent } from './core/i18n/root-redirect.guard';

export const routes: Routes = [
  // '' → composant qui redirige impérativement vers /<lang>
  { path: '', component: RootRedirectComponent },

  // /:lang/... protégé par le guard
  {
    path: ':lang',
    canMatch: [languageUrlGuard],
    children: [
      { path: '', component: HomeComponent },
      { path: 'about', component: AboutComponent },
      { path: 'settings', component: SettingsComponent },
      { path: '**', redirectTo: '' },
      { path: 'auth/register', loadComponent: () => import('./features/auth/register-page.component').then(m => m.RegisterPageComponent) }
    ],
  },

  { path: '**', redirectTo: '' },
];
