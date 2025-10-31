import { Directive, ElementRef, Input, OnInit, Renderer2 } from '@angular/core';

/**
 * Directive pour créer des liens de navigation rapide (skip links)
 * Permet aux utilisateurs de clavier/lecteur d'écran de sauter directement au contenu
 *
 * @example
 * <a skipLink target="#main-content">Aller au contenu principal</a>
 * ...
 * <main id="main-content">...</main>
 */
@Directive({
  selector: '[skipLink]',
  standalone: true,
})
export class SkipLinkDirective implements OnInit {
  /** ID de la cible vers laquelle naviguer */
  @Input() target = '#main-content';

  constructor(
    private el: ElementRef<HTMLAnchorElement>,
    private renderer: Renderer2
  ) {}

  ngOnInit(): void {
    const element = this.el.nativeElement;

    // Ajouter la classe CSS
    this.renderer.addClass(element, 'skip-link');

    // Définir l'attribut href
    this.renderer.setAttribute(element, 'href', this.target);

    // Ajouter l'événement click pour focus
    this.renderer.listen(element, 'click', (event: Event) => {
      event.preventDefault();
      this.focusTarget();
    });
  }

  private focusTarget(): void {
    const targetElement = document.querySelector(this.target) as HTMLElement;

    if (targetElement) {
      // Si l'élément n'est pas focusable, le rendre temporairement focusable
      if (!targetElement.hasAttribute('tabindex')) {
        targetElement.setAttribute('tabindex', '-1');
      }

      // Focus sur l'élément
      targetElement.focus();

      // Scroll vers l'élément
      targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}
