import {FaqComponent} from "@shared/components/faq/faq";
import {About} from "@shared/components/about/about";
import {LoginPageComponent} from "@app/login-page/login-page";
import {RegisterPageComponent} from "@app/upload/register-page/register-page";
import {guestGuard} from "@core/http";
import {languageUrlGuard} from "@core/i18n";
import {Routes} from "@angular/router";
import {HomeComponent} from "@app/features/home/home.component";
import {EventListMockComponent} from "@app/event-list-mock/event-list-mock";
import {EventDetailMockComponent} from "@app/event-detail-mock/event-detail-mock";

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
      { path: 'events/:id', component: EventDetailMockComponent }, // ← corrigé

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
      { path: 'faq', component: FaqComponent },
      { path: 'about', component: About },
      { path: '**', redirectTo: '' },
    ],
  },

  { path: '**', redirectTo: '/fr' },
];
