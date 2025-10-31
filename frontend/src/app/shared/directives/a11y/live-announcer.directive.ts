import {
  Directive,
  ElementRef,
  Input,
  OnChanges,
  SimpleChanges,
  Renderer2,
} from '@angular/core';

export type PolitenessLevel = 'polite' | 'assertive' | 'off';

/**
 * Directive pour créer des live regions (annonces pour lecteurs d'écran)
 * Annonce les changements de contenu aux utilisateurs de lecteurs d'écran
 *
 * @example
 * <div liveAnnouncer [politeness]="'polite'" [announce]="message">
 *   {{ message }}
 * </div>
 *
 * @example Zone de statut
 * <div liveAnnouncer="polite" role="status">
 *   Chargement en cours...
 * </div>
 */
@Directive({
  selector: '[liveAnnouncer]',
  standalone: true,
})
export class LiveAnnouncerDirective implements OnChanges {
  /** Niveau de politesse de l'annonce */
  @Input() liveAnnouncer: PolitenessLevel = 'polite';

  /** Alias pour politeness */
  @Input() politeness?: PolitenessLevel;

  /** Message à annoncer (quand il change) */
  @Input() announce?: string;

  /** Annoncer le contenu atomiquement (toute la zone) */
  @Input() atomic = true;

  /** Rôle ARIA (status ou alert) */
  @Input() role?: 'status' | 'alert';

  private previousAnnouncement?: string;

  constructor(
    private el: ElementRef<HTMLElement>,
    private renderer: Renderer2
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    const element = this.el.nativeElement;

    // Déterminer le niveau de politesse
    const politeness = this.politeness || this.liveAnnouncer;

    // Configurer les attributs ARIA
    this.renderer.setAttribute(element, 'aria-live', politeness);
    this.renderer.setAttribute(element, 'aria-atomic', String(this.atomic));

    // Définir le rôle
    if (this.role) {
      this.renderer.setAttribute(element, 'role', this.role);
    } else if (politeness === 'assertive') {
      this.renderer.setAttribute(element, 'role', 'alert');
    } else if (politeness === 'polite') {
      this.renderer.setAttribute(element, 'role', 'status');
    }

    // Annoncer si le message a changé
    if (changes['announce'] && this.announce !== this.previousAnnouncement) {
      this.makeAnnouncement(this.announce);
      this.previousAnnouncement = this.announce;
    }
  }

  private makeAnnouncement(message?: string): void {
    if (!message) return;

    const element = this.el.nativeElement;

    // Vider puis remplir pour forcer l'annonce
    this.renderer.setProperty(element, 'textContent', '');

    setTimeout(() => {
      this.renderer.setProperty(element, 'textContent', message);
    }, 100);
  }
}
