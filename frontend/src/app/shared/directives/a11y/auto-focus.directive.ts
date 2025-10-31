import {
  Directive,
  ElementRef,
  Input,
  OnInit,
  AfterViewInit,
} from '@angular/core';

/**
 * Directive pour gérer le focus automatique de manière accessible
 * Utilise setTimeout pour éviter les problèmes avec les lecteurs d'écran
 *
 * @example
 * <input autoFocus [autoFocusDelay]="100">
 *
 * @example Avec condition
 * <input [autoFocus]="shouldFocus">
 */
@Directive({
  selector: '[autoFocus]',
  standalone: true,
})
export class AutoFocusDirective implements OnInit, AfterViewInit {
  /** Activer/désactiver le focus automatique */
  @Input() autoFocus: boolean | '' = true;

  /** Délai avant le focus (pour la compatibilité lecteur d'écran) */
  @Input() autoFocusDelay = 100;

  constructor(private el: ElementRef<HTMLElement>) {}

  ngOnInit(): void {
    // La logique est dans AfterViewInit pour s'assurer que le DOM est prêt
  }

  ngAfterViewInit(): void {
    const shouldFocus = this.autoFocus === '' || this.autoFocus === true;

    if (shouldFocus) {
      // Utiliser setTimeout pour éviter les problèmes avec les lecteurs d'écran
      setTimeout(() => {
        this.el.nativeElement.focus();
      }, this.autoFocusDelay);
    }
  }
}
