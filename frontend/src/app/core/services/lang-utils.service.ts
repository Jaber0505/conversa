import { Injectable, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

/**
 * Service utilitaire pour la gestion de la langue dans les routes
 * Centralise la logique de récupération de la langue depuis les paramètres de route
 */
@Injectable({ providedIn: 'root' })
export class LangUtilsService {
  private route = inject(ActivatedRoute);

  /**
   * Récupère la langue depuis les paramètres de route
   * Remonte l'arborescence des routes si nécessaire
   * @returns Code de langue (fr, en, nl) ou 'fr' par défaut
   */
  getLanguageFromRoute(route?: ActivatedRoute): string {
    let r: ActivatedRoute | null = route || this.route;
    while (r) {
      const v = r.snapshot.paramMap.get('lang');
      if (v) return v;
      r = r.parent;
    }
    return 'fr';
  }

  /**
   * Raccourci pour récupérer la langue courante
   */
  get current(): string {
    return this.getLanguageFromRoute();
  }
}
