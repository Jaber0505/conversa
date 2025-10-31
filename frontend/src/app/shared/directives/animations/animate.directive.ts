import { Directive, ElementRef, Input, OnInit, Renderer2 } from '@angular/core';

export type AnimationType =
  | 'fadeIn'
  | 'fadeInUp'
  | 'fadeInDown'
  | 'fadeInLeft'
  | 'fadeInRight'
  | 'scaleIn'
  | 'slideInUp'
  | 'slideInDown'
  | 'fadeOut'
  | 'fadeOutUp'
  | 'fadeOutDown'
  | 'scaleOut'
  | 'pulse'
  | 'bounce'
  | 'shake'
  | 'wiggle'
  | 'heartbeat'
  | 'spin';

export type AnimationDuration = 'instant' | 'fast' | 'normal' | 'slow' | 'slower';

/**
 * Directive pour appliquer des animations CSS aux éléments
 *
 * @example
 * <div animate="fadeInUp" [animateDuration]="'fast'" [animateDelay]="100">
 *   Contenu animé
 * </div>
 *
 * @example
 * <div animate="scaleIn" [animateOnce]="true">
 *   Animation une seule fois
 * </div>
 */
@Directive({
  selector: '[animate]',
  standalone: true,
})
export class AnimateDirective implements OnInit {
  /** Type d'animation à appliquer */
  @Input() animate: AnimationType = 'fadeIn';

  /** Durée de l'animation */
  @Input() animateDuration: AnimationDuration = 'normal';

  /** Délai avant le démarrage (en ms) */
  @Input() animateDelay = 0;

  /** Jouer l'animation une seule fois (par défaut: true) */
  @Input() animateOnce = true;

  /** Fonction d'easing personnalisée */
  @Input() animateEasing?: string;

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
    this.applyAnimation();
  }

  private applyAnimation(): void {
    const element = this.el.nativeElement;

    // Appliquer le nom de l'animation
    this.renderer.setStyle(element, 'animation-name', this.animate);

    // Appliquer la durée
    const duration = this.durationMap[this.animateDuration];
    this.renderer.setStyle(element, 'animation-duration', duration);

    // Appliquer le délai
    if (this.animateDelay > 0) {
      this.renderer.setStyle(element, 'animation-delay', `${this.animateDelay}ms`);
    }

    // Appliquer l'easing personnalisé ou par défaut
    const easing = this.animateEasing || 'var(--ease-out-expo)';
    this.renderer.setStyle(element, 'animation-timing-function', easing);

    // Fill mode pour garder l'état final
    if (this.animateOnce) {
      this.renderer.setStyle(element, 'animation-fill-mode', 'both');
      this.renderer.setStyle(element, 'animation-iteration-count', '1');
    }
  }
}
