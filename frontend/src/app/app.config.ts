// frontend/src/app/app.config.ts
import { ApplicationConfig, provideEnvironmentInitializer, inject } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors, withInterceptorsFromDi } from '@angular/common/http';

import { routes } from './app.routes';

// i18n via barrel
import { acceptLanguageInterceptor, I18nService, LangService } from '@i18n';

// autres interceptors/fournisseurs app
import { authInterceptor } from './core/http/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),

    provideHttpClient(
      withInterceptors([acceptLanguageInterceptor, authInterceptor]),
      withInterceptorsFromDi()
    ),

    provideEnvironmentInitializer(() => {
      const i18n = inject(I18nService);
      const current = inject(LangService).current;
      void i18n.preload(current);
    }),
  ],
};
