import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { CanActivateFn } from '@angular/router';
import { AuthTokenService } from '@core/http';

/**
 * Guard pour la homepage
 * Redirige les utilisateurs connectés vers /events
 * Autorise les visiteurs non connectés
 */
export const homeGuard: CanActivateFn = (route, state) => {
  const authTokenService = inject(AuthTokenService);
  const router = inject(Router);

  // Vérifier si l'utilisateur est connecté
  const isAuthenticated = authTokenService.hasAccess();

  if (isAuthenticated) {
    // Utilisateur connecté → Redirection vers /events
    const lang = route.paramMap.get('lang') || 'fr';
    router.navigate(['/', lang, 'events']);
    return false;
  }

  // Visiteur non connecté → Accès autorisé à la homepage
  return true;
};
