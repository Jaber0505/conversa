import { Component, Input, HostBinding, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'shared-grid',
  standalone: true,
  templateUrl: './grid.component.html',
  styleUrls: ['./grid.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GridComponent {
  /** Colonnes par breakpoint (mobile-first) */
  @Input() cols = 1;
  @Input() colsSm?: number;
  @Input() colsMd?: number;
  @Input() colsLg?: number;

  /** Espacement (gap CSS — ex: "1rem" ou "var(--space-6)") */
  @Input() gap = 'var(--space-6)';

  @HostBinding('style.--cols')    get c()  { return String(this.cols); }
  @HostBinding('style.--cols-sm') get cs() { return this.colsSm ? String(this.colsSm) : null; }
  @HostBinding('style.--cols-md') get cm() { return this.colsMd ? String(this.colsMd) : null; }
  @HostBinding('style.--cols-lg') get cl() { return this.colsLg ? String(this.colsLg) : null; }
  @HostBinding('style.--gap')     get g()  { return this.gap; }
}
