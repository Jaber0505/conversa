import { Routes } from '@angular/router';
import { HomeComponent } from './features/home/home.component';

// ⬇️ i18n guard via barrel
import { languageUrlGuard } from '@i18n';

export const routes: Routes = [
  { path: '', redirectTo: '/fr', pathMatch: 'full' },
  {
    path: ':lang',
    canMatch: [languageUrlGuard],
    children: [
      { path: '', component: HomeComponent },
      { path: 'auth', children: [] },
      { path: '**', redirectTo: '' },
    ],
  },
  { path: '**', redirectTo: '/fr' },
];
