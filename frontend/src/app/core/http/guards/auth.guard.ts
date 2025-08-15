import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthTokenService } from '../auth-token.service';
import { LangService } from '@i18n';

export const authGuard: CanActivateFn = (_route, state) => {
  const tokens = inject(AuthTokenService);
  if (tokens.access) return true; // connecté → accès OK

  const lang = inject(LangService).current;
  const router = inject(Router);
  // non connecté → login avec redirection vers la page demandée
  return router.createUrlTree(['/', lang, 'auth', 'login'], {
    queryParams: { redirect: state.url },
  });
};
