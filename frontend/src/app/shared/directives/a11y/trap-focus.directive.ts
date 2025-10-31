import {
  Directive,
  ElementRef,
  Input,
  OnInit,
  OnDestroy,
  HostListener,
} from '@angular/core';

/**
 * Directive pour piéger le focus dans un conteneur (utile pour les modales)
 * Empêche le focus de sortir du conteneur lors de la navigation au clavier
 *
 * @example
 * <div trapFocus [trapActive]="isModalOpen">
 *   <button>Premier élément focusable</button>
 *   <input type="text">
 *   <button>Dernier élément focusable</button>
 * </div>
 */
@Directive({
  selector: '[trapFocus]',
  standalone: true,
})
export class TrapFocusDirective implements OnInit, OnDestroy {
  /** Activer/désactiver le piège à focus */
  @Input() trapActive = true;

  /** Focus automatiquement le premier élément au montage */
  @Input() autoFocusFirst = true;

  private firstFocusableElement?: HTMLElement;
  private lastFocusableElement?: HTMLElement;
  private previouslyFocusedElement?: HTMLElement;

  private readonly focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(', ');

  constructor(private el: ElementRef<HTMLElement>) {}

  ngOnInit(): void {
    if (this.trapActive) {
      this.activate();
    }
  }

  ngOnDestroy(): void {
    this.deactivate();
  }

  @HostListener('keydown', ['$event'])
  handleKeydown(event: KeyboardEvent): void {
    if (!this.trapActive) return;

    if (event.key === 'Tab') {
      this.handleTabKey(event);
    } else if (event.key === 'Escape') {
      this.handleEscapeKey();
    }
  }

  private activate(): void {
    // Sauvegarder l'élément actuellement focusé
    this.previouslyFocusedElement = document.activeElement as HTMLElement;

    // Trouver les éléments focusables
    this.updateFocusableElements();

    // Focus le premier élément
    if (this.autoFocusFirst && this.firstFocusableElement) {
      setTimeout(() => {
        this.firstFocusableElement?.focus();
      }, 100);
    }
  }

  private deactivate(): void {
    // Restaurer le focus précédent
    if (this.previouslyFocusedElement) {
      this.previouslyFocusedElement.focus();
    }
  }

  private updateFocusableElements(): void {
    const focusableElements = this.el.nativeElement.querySelectorAll<HTMLElement>(
      this.focusableSelectors
    );

    if (focusableElements.length === 0) return;

    this.firstFocusableElement = focusableElements[0];
    this.lastFocusableElement = focusableElements[focusableElements.length - 1];
  }

  private handleTabKey(event: KeyboardEvent): void {
    if (!this.firstFocusableElement || !this.lastFocusableElement) {
      return;
    }

    // Shift + Tab sur le premier élément -> aller au dernier
    if (event.shiftKey && document.activeElement === this.firstFocusableElement) {
      event.preventDefault();
      this.lastFocusableElement.focus();
    }
    // Tab sur le dernier élément -> aller au premier
    else if (!event.shiftKey && document.activeElement === this.lastFocusableElement) {
      event.preventDefault();
      this.firstFocusableElement.focus();
    }
  }

  private handleEscapeKey(): void {
    // Émettre un événement personnalisé pour fermer la modale/conteneur
    const event = new CustomEvent('escapeFocusTrap', {
      bubbles: true,
      cancelable: true,
    });

    this.el.nativeElement.dispatchEvent(event);
  }
}
