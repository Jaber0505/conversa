import { Component, Input, HostBinding } from '@angular/core';
import { CommonModule } from '@angular/common';

type ColSpan = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 'full' | 'auto';
type Order = 'first' | 'last' | 'none' | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;

/**
 * Composant Grid Item pour contrôler le comportement des enfants de grille
 *
 * @example Span responsive
 * <shared-grid-item [span]="12" [spanMd]="6" [spanLg]="4">
 *   Full width mobile, 50% tablet, 33% desktop
 * </shared-grid-item>
 *
 * @example Start/End
 * <shared-grid-item [start]="2" [end]="5">
 *   Occupe colonnes 2 à 4
 * </shared-grid-item>
 *
 * @example Order
 * <shared-grid-item [order]="'last'">
 *   Apparaît en dernier
 * </shared-grid-item>
 */
@Component({
  selector: 'shared-grid-item',
  standalone: true,
  imports: [CommonModule],
  template: '<ng-content></ng-content>',
  styles: [
    `
      :host {
        display: block;
      }
    `,
  ],
})
export class GridItemComponent {
  /** Nombre de colonnes à occuper (mobile) */
  @Input() span: ColSpan = 'auto';

  /** Nombre de colonnes à occuper (sm - 640px+) */
  @Input() spanSm?: ColSpan;

  /** Nombre de colonnes à occuper (md - 768px+) */
  @Input() spanMd?: ColSpan;

  /** Nombre de colonnes à occuper (lg - 1024px+) */
  @Input() spanLg?: ColSpan;

  /** Nombre de colonnes à occuper (xl - 1280px+) */
  @Input() spanXl?: ColSpan;

  /** Colonne de départ */
  @Input() start?: number;

  /** Colonne de fin */
  @Input() end?: number;

  /** Ordre d'affichage */
  @Input() order?: Order;

  /** Ordre d'affichage (md) */
  @Input() orderMd?: Order;

  /** Ordre d'affichage (lg) */
  @Input() orderLg?: Order;

  /** Classes CSS personnalisées */
  @Input() customClass = '';

  @HostBinding('class')
  get hostClasses(): string {
    const classes: string[] = [];

    // Span
    classes.push(this.getSpanClass('', this.span));
    if (this.spanSm) classes.push(this.getSpanClass('sm', this.spanSm));
    if (this.spanMd) classes.push(this.getSpanClass('md', this.spanMd));
    if (this.spanLg) classes.push(this.getSpanClass('lg', this.spanLg));
    if (this.spanXl) classes.push(this.getSpanClass('xl', this.spanXl));

    // Start/End
    if (this.start) classes.push(`col-start-${this.start}`);
    if (this.end) classes.push(`col-end-${this.end}`);

    // Order
    if (this.order) classes.push(this.getOrderClass('', this.order));
    if (this.orderMd) classes.push(this.getOrderClass('md', this.orderMd));
    if (this.orderLg) classes.push(this.getOrderClass('lg', this.orderLg));

    // Custom classes
    if (this.customClass) classes.push(this.customClass);

    return classes.join(' ');
  }

  private getSpanClass(breakpoint: string, span: ColSpan): string {
    const prefix = breakpoint ? `col-span-${breakpoint}-` : 'col-span-';
    return `${prefix}${span}`;
  }

  private getOrderClass(breakpoint: string, order: Order): string {
    const prefix = breakpoint ? `order-${breakpoint}-` : 'order-';
    return `${prefix}${order}`;
  }
}
