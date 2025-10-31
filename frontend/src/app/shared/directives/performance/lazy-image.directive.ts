import {
  Directive,
  ElementRef,
  Input,
  OnInit,
  OnDestroy,
  Renderer2,
} from '@angular/core';

/**
 * Directive pour lazy loading d'images avec IntersectionObserver
 * Charge l'image uniquement quand elle est proche du viewport
 *
 * @example
 * <img lazyImage [src]="imageUrl" [placeholder]="placeholderUrl" alt="Description">
 *
 * @example Avec WebP
 * <img lazyImage [src]="'image.webp'" [fallback]="'image.jpg'" alt="Description">
 */
@Directive({
  selector: 'img[lazyImage]',
  standalone: true,
})
export class LazyImageDirective implements OnInit, OnDestroy {
  /** URL de l'image à charger */
  @Input() src = '';

  /** URL de l'image placeholder (basse résolution) */
  @Input() placeholder?: string;

  /** URL de fallback si WebP n'est pas supporté */
  @Input() fallback?: string;

  /** Marge avant de charger l'image (px) */
  @Input() rootMargin = '50px';

  /** Seuil de visibilité (0-1) */
  @Input() threshold = 0.01;

  private observer?: IntersectionObserver;
  private isLoaded = false;

  constructor(
    private el: ElementRef<HTMLImageElement>,
    private renderer: Renderer2
  ) {}

  ngOnInit(): void {
    // Définir le placeholder initial
    if (this.placeholder) {
      this.renderer.setAttribute(this.el.nativeElement, 'src', this.placeholder);
    } else {
      // Placeholder SVG inline (1x1px transparent)
      const placeholder =
        'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E';
      this.renderer.setAttribute(this.el.nativeElement, 'src', placeholder);
    }

    // Ajouter loading="lazy" natif comme fallback
    this.renderer.setAttribute(this.el.nativeElement, 'loading', 'lazy');

    // Ajouter classe pour le style
    this.renderer.addClass(this.el.nativeElement, 'lazy-image');
    this.renderer.addClass(this.el.nativeElement, 'lazy-image--loading');

    // Créer l'observer
    this.createObserver();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }

  private createObserver(): void {
    const options: IntersectionObserverInit = {
      rootMargin: this.rootMargin,
      threshold: this.threshold,
    };

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !this.isLoaded) {
          this.loadImage();
        }
      });
    }, options);

    this.observer.observe(this.el.nativeElement);
  }

  private loadImage(): void {
    const img = this.el.nativeElement;

    // Créer une nouvelle image pour précharger
    const tempImg = new Image();

    tempImg.onload = () => {
      // L'image est chargée, l'afficher
      this.renderer.setAttribute(img, 'src', this.src);
      this.renderer.removeClass(img, 'lazy-image--loading');
      this.renderer.addClass(img, 'lazy-image--loaded');
      this.isLoaded = true;

      // Déconnecter l'observer
      this.observer?.disconnect();
    };

    tempImg.onerror = () => {
      // Erreur de chargement, essayer le fallback
      if (this.fallback) {
        this.renderer.setAttribute(img, 'src', this.fallback);
      }

      this.renderer.removeClass(img, 'lazy-image--loading');
      this.renderer.addClass(img, 'lazy-image--error');
      this.isLoaded = true;
    };

    // Démarrer le chargement
    tempImg.src = this.src;
  }
}
