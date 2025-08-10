/**
 * Configuration globale de l'application (Angular standalone).
 * Fournit HttpClient (moderne) et le Router à partir des routes déclarées.
 * Point d’extension idéal pour ajouter interceptors/guards plus tard.
 */
// src/app/app.config.ts
import { ApplicationConfig, provideEnvironmentInitializer, inject } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors, withInterceptorsFromDi } from '@angular/common/http';
import { routes } from './app.routes';
import { acceptLanguageInterceptor } from './core/i18n/accept-language.interceptor';
import { I18nService } from '@app/core/i18n/i18n.service';
import { LangService } from '@app/core/i18n/lang.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([acceptLanguageInterceptor]),
      withInterceptorsFromDi()
    ),

    provideEnvironmentInitializer(() => {
      const i18n = inject(I18nService);
      const current = inject(LangService).current;
      void i18n.preload(current);
    }),
  ],
};

