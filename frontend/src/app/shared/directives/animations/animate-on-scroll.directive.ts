import {
  Directive,
  ElementRef,
  Input,
  OnInit,
  OnDestroy,
  Renderer2,
} from '@angular/core';
import { AnimationType, AnimationDuration } from './animate.directive';

/**
 * Directive pour déclencher une animation quand l'élément entre dans le viewport
 *
 * Utilise l'Intersection Observer API pour la performance
 *
 * @example
 * <div animateOnScroll="fadeInUp" [animateThreshold]="0.2">
 *   Apparaît en scrollant
 * </div>
 */
@Directive({
  selector: '[animateOnScroll]',
  standalone: true,
})
export class AnimateOnScrollDirective implements OnInit, OnDestroy {
  /** Type d'animation à appliquer */
  @Input() animateOnScroll: AnimationType = 'fadeInUp';

  /** Durée de l'animation */
  @Input() animateDuration: AnimationDuration = 'normal';

  /** Délai avant le démarrage de l'animation (en millisecondes) */
  @Input() animateDelay = 0;

  /** Seuil de visibilité (0-1) pour déclencher l'animation */
  @Input() animateThreshold = 0.1;

  /** Rejouer l'animation à chaque fois que l'élément entre dans le viewport */
  @Input() animateRepeat = false;

  private observer?: IntersectionObserver;
  private hasAnimated = false;

  private readonly durationMap: Record<AnimationDuration, string> = {
    instant: '50ms',
    fast: '120ms',
    normal: '200ms',
    slow: '300ms',
    slower: '500ms',
  };

  constructor(
    private el: ElementRef<HTMLElement>,
    private renderer: Renderer2
  ) {}

  ngOnInit(): void {
    // Cacher l'élément initialement
    this.renderer.setStyle(this.el.nativeElement, 'opacity', '0');

    // Créer l'observer
    this.createObserver();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }

  private createObserver(): void {
    const options: IntersectionObserverInit = {
      threshold: this.animateThreshold,
      rootMargin: '0px',
    };

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // L'élément est visible
          if (!this.hasAnimated || this.animateRepeat) {
            this.playAnimation();
            this.hasAnimated = true;

            // Si on ne veut pas répéter, déconnecter l'observer
            if (!this.animateRepeat) {
              this.observer?.disconnect();
            }
          }
        } else if (this.animateRepeat) {
          // Réinitialiser pour la prochaine fois
          this.resetAnimation();
        }
      });
    }, options);

    this.observer.observe(this.el.nativeElement);
  }

  private playAnimation(): void {
    const element = this.el.nativeElement;

    // Appliquer le délai si spécifié
    setTimeout(() => {
      // Réinitialiser l'opacité
      this.renderer.setStyle(element, 'opacity', '1');

      // Appliquer l'animation
      this.renderer.setStyle(element, 'animation-name', this.animateOnScroll);
      this.renderer.setStyle(
        element,
        'animation-duration',
        this.durationMap[this.animateDuration]
      );
      this.renderer.setStyle(element, 'animation-timing-function', 'var(--ease-out-expo)');
      this.renderer.setStyle(element, 'animation-fill-mode', 'both');
    }, this.animateDelay);
  }

  private resetAnimation(): void {
    const element = this.el.nativeElement;
    this.renderer.setStyle(element, 'animation-name', 'none');
    this.renderer.setStyle(element, 'opacity', '0');

    // Force reflow pour réinitialiser l'animation
    void element.offsetWidth;
  }
}
