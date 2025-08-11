import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { languageUrlGuard } from './core/i18n/language-url.guard';

export const routes: Routes = [
    {
        path: '',
        redirectTo: '/fr',
        pathMatch: 'full'
    },
    {
        path: ':lang',
        canMatch: [languageUrlGuard],
        children: [
            {
                path: '',
                component: HomeComponent
            },
            {
                path: 'auth',
                children: [
                    {
                        path: 'register',
                        loadComponent: () =>
                            import('./features/auth/register-page.component')
                                .then(m => m.RegisterPageComponent)
                    }
                ]
            },
            // exemples à réactiver ensuite :
            // { path: 'events', loadComponent: () => import('./features/events/events-page.component').then(m => m.EventsPageComponent) },
            // { path: 'about',  loadComponent: () => import('./features/about/about-page.component').then(m => m.AboutPageComponent) },
            // { path: 'faq',    loadComponent: () => import('./features/faq/faq-page.component').then(m => m.FaqPageComponent) },
            { path: '**', redirectTo: '' }
        ]
    },
    {
        path: '**',
        redirectTo: '/fr'
    }
];
