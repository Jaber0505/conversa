import { Injectable, ApplicationRef, ComponentRef, createComponent, EnvironmentInjector } from '@angular/core';

export type AnnouncementPoliteness = 'polite' | 'assertive';

/**
 * Service pour annoncer des messages aux lecteurs d'écran
 * Crée dynamiquement une live region ARIA
 *
 * @example
 * constructor(private announcer: LiveAnnouncerService) {}
 *
 * onSave() {
 *   this.announcer.announce('Sauvegarde réussie', 'polite');
 * }
 *
 * onError() {
 *   this.announcer.announce('Erreur lors de la sauvegarde', 'assertive');
 * }
 */
@Injectable({
  providedIn: 'root',
})
export class LiveAnnouncerService {
  private liveElement?: HTMLElement;

  constructor(
    private appRef: ApplicationRef,
    private injector: EnvironmentInjector
  ) {
    this.createLiveRegion();
  }

  /**
   * Annonce un message aux lecteurs d'écran
   * @param message Message à annoncer
   * @param politeness Niveau de politesse ('polite' | 'assertive')
   * @param duration Durée d'affichage du message (ms), 0 = permanent
   */
  announce(
    message: string,
    politeness: AnnouncementPoliteness = 'polite',
    duration = 3000
  ): void {
    if (!this.liveElement) {
      this.createLiveRegion();
    }

    if (!this.liveElement) return;

    // Configurer la politesse
    this.liveElement.setAttribute('aria-live', politeness);

    // Vider puis annoncer (force le lecteur d'écran à relire)
    this.liveElement.textContent = '';

    setTimeout(() => {
      if (this.liveElement) {
        this.liveElement.textContent = message;

        // Effacer après la durée spécifiée
        if (duration > 0) {
          setTimeout(() => {
            if (this.liveElement) {
              this.liveElement.textContent = '';
            }
          }, duration);
        }
      }
    }, 100);
  }

  /**
   * Annonce un message avec politesse 'polite'
   */
  announcePolite(message: string, duration = 3000): void {
    this.announce(message, 'polite', duration);
  }

  /**
   * Annonce un message avec politesse 'assertive' (urgent)
   */
  announceAssertive(message: string, duration = 5000): void {
    this.announce(message, 'assertive', duration);
  }

  /**
   * Efface le message en cours
   */
  clear(): void {
    if (this.liveElement) {
      this.liveElement.textContent = '';
    }
  }

  private createLiveRegion(): void {
    // Vérifier si déjà créé
    if (this.liveElement) return;

    // Créer l'élément
    this.liveElement = document.createElement('div');
    this.liveElement.setAttribute('aria-live', 'polite');
    this.liveElement.setAttribute('aria-atomic', 'true');
    this.liveElement.setAttribute('role', 'status');

    // Styles pour masquer visuellement (sr-only)
    Object.assign(this.liveElement.style, {
      position: 'absolute',
      width: '1px',
      height: '1px',
      padding: '0',
      margin: '-1px',
      overflow: 'hidden',
      clip: 'rect(0, 0, 0, 0)',
      whiteSpace: 'nowrap',
      borderWidth: '0',
    });

    // Ajouter au DOM
    document.body.appendChild(this.liveElement);
  }

  /**
   * Détruit la live region (cleanup)
   */
  destroy(): void {
    if (this.liveElement) {
      document.body.removeChild(this.liveElement);
      this.liveElement = undefined;
    }
  }
}
