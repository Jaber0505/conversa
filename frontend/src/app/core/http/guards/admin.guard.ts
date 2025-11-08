import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { inject } from '@angular/core';
import { AuthApiService, AuthTokenService } from '@core/http';
import { LangService } from '@core/i18n';
import { map, catchError, of } from 'rxjs';

/**
 * Admin-only guard: autorise l'accès uniquement si l'utilisateur est admin (is_staff).
 * - Redirige vers /:lang (accueil) si non admin ou non authentifié
 */
export const adminGuard: CanActivateFn = () => {
  const tokens = inject(AuthTokenService);
  const api = inject(AuthApiService);
  const router = inject(Router);
  const lang = inject(LangService).current;

  if (!tokens.hasAccess()) {
    // Non connecté → retour à l'accueil (authGuard devrait déjà filtrer en amont)
    return router.createUrlTree(['/', lang]);
  }

  return api.me().pipe(
    map((me) => (me && (me as any).is_staff) ? true : (router.createUrlTree(['/', lang]) as UrlTree)),
    catchError(() => of(router.createUrlTree(['/', lang]) as UrlTree))
  );
};

