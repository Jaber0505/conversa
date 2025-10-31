import { Component, Input, HostBinding } from '@angular/core';
import { CommonModule } from '@angular/common';

type GridCols = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 'auto-fit' | 'auto-fill';
type Gap = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12;
type JustifyItems = 'start' | 'end' | 'center' | 'stretch';
type AlignItems = 'start' | 'end' | 'center' | 'stretch' | 'baseline';

/**
 * Composant Grid avancé avec support responsive complet
 *
 * @example
 * <shared-advanced-grid [cols]="12" [colsMd]="6" [colsLg]="4" [gap]="4">
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </shared-advanced-grid>
 *
 * @example Layout sidebar
 * <shared-advanced-grid [cols]="1" [colsLg]="'sidebar-left'" [gap]="6">
 *   <aside>Sidebar</aside>
 *   <main>Content</main>
 * </shared-advanced-grid>
 */
@Component({
  selector: 'shared-advanced-grid',
  standalone: true,
  imports: [CommonModule],
  template: '<ng-content></ng-content>',
  styles: [
    `
      :host {
        display: grid;
        width: 100%;
      }
    `,
  ],
})
export class AdvancedGridComponent {
  /** Nombre de colonnes (mobile) */
  @Input() cols: GridCols = 1;

  /** Nombre de colonnes (sm - 640px+) */
  @Input() colsSm?: GridCols;

  /** Nombre de colonnes (md - 768px+) */
  @Input() colsMd?: GridCols;

  /** Nombre de colonnes (lg - 1024px+) */
  @Input() colsLg?: GridCols;

  /** Nombre de colonnes (xl - 1280px+) */
  @Input() colsXl?: GridCols;

  /** Gap entre les éléments */
  @Input() gap: Gap = 4;

  /** Gap horizontal uniquement */
  @Input() gapX?: Gap;

  /** Gap vertical uniquement */
  @Input() gapY?: Gap;

  /** Justification horizontale des items */
  @Input() justifyItems?: JustifyItems;

  /** Alignement vertical des items */
  @Input() alignItems?: AlignItems;

  /** Flow direction */
  @Input() flow?: 'row' | 'col' | 'dense' | 'row-dense' | 'col-dense';

  /** Classes CSS personnalisées */
  @Input() customClass = '';

  @HostBinding('class')
  get hostClasses(): string {
    const classes: string[] = [];

    // Colonnes
    classes.push(this.getColClass('', this.cols));
    if (this.colsSm) classes.push(this.getColClass('sm', this.colsSm));
    if (this.colsMd) classes.push(this.getColClass('md', this.colsMd));
    if (this.colsLg) classes.push(this.getColClass('lg', this.colsLg));
    if (this.colsXl) classes.push(this.getColClass('xl', this.colsXl));

    // Gaps
    if (this.gapX !== undefined) {
      classes.push(`gap-x-${this.gapX}`);
    } else if (this.gapY !== undefined) {
      classes.push(`gap-y-${this.gapY}`);
    } else {
      classes.push(`gap-${this.gap}`);
    }

    // Alignement
    if (this.justifyItems) classes.push(`justify-items-${this.justifyItems}`);
    if (this.alignItems) classes.push(`align-items-${this.alignItems}`);

    // Flow
    if (this.flow) classes.push(`grid-flow-${this.flow}`);

    // Custom classes
    if (this.customClass) classes.push(this.customClass);

    return classes.join(' ');
  }

  private getColClass(breakpoint: string, cols: GridCols): string {
    const prefix = breakpoint ? `grid-cols-${breakpoint}-` : 'grid-cols-';

    if (cols === 'auto-fit' || cols === 'auto-fill') {
      return `grid-cols-${cols}`;
    }

    return `${prefix}${cols}`;
  }
}
