import {
  Directive,
  ElementRef,
  Input,
  OnInit,
  OnDestroy,
  TemplateRef,
  ViewContainerRef,
  EmbeddedViewRef,
} from '@angular/core';

/**
 * Directive pour lazy loading de contenu (defer loading)
 * Ne charge le contenu que quand il est visible dans le viewport
 *
 * @example
 * <ng-container *deferLoad>
 *   <heavy-component></heavy-component>
 * </ng-container>
 *
 * @example Avec paramètres
 * <ng-container *deferLoad="{ rootMargin: '200px', threshold: 0.1 }">
 *   <expensive-chart></expensive-chart>
 * </ng-container>
 */
@Directive({
  selector: '[deferLoad]',
  standalone: true,
})
export class DeferLoadDirective implements OnInit, OnDestroy {
  /** Configuration de l'intersection observer */
  @Input() deferLoad: {
    rootMargin?: string;
    threshold?: number;
  } = {};

  private observer?: IntersectionObserver;
  private viewRef?: EmbeddedViewRef<any>;
  private placeholderElement?: HTMLElement;

  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef
  ) {}

  ngOnInit(): void {
    // Créer un élément placeholder
    this.placeholderElement = document.createElement('div');
    this.placeholderElement.style.minHeight = '1px';

    // Insérer le placeholder dans le ViewContainer
    this.viewContainer.clear();
    const hostElement = (this.viewContainer.element.nativeElement as HTMLElement)
      .parentElement;

    if (hostElement) {
      hostElement.appendChild(this.placeholderElement);
    }

    // Créer l'observer
    this.createObserver();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();

    if (this.placeholderElement && this.placeholderElement.parentElement) {
      this.placeholderElement.parentElement.removeChild(this.placeholderElement);
    }
  }

  private createObserver(): void {
    if (!this.placeholderElement) return;

    const options: IntersectionObserverInit = {
      rootMargin: this.deferLoad.rootMargin || '50px',
      threshold: this.deferLoad.threshold || 0.01,
    };

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !this.viewRef) {
          this.loadContent();
        }
      });
    }, options);

    this.observer.observe(this.placeholderElement);
  }

  private loadContent(): void {
    // Charger le template
    this.viewRef = this.viewContainer.createEmbeddedView(this.templateRef);

    // Supprimer le placeholder
    if (this.placeholderElement && this.placeholderElement.parentElement) {
      this.placeholderElement.parentElement.removeChild(this.placeholderElement);
    }

    // Déconnecter l'observer
    this.observer?.disconnect();
  }
}
