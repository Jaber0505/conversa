import {
  Component,
  Input,
  Output,
  EventEmitter,
  TemplateRef,
  ChangeDetectionStrategy,
  OnInit,
  OnDestroy,
  HostListener,
  ElementRef,
  ViewChild,
  AfterViewInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * Composant Virtual Scroll pour afficher de grandes listes efficacement
 * Recycle les éléments DOM pour de meilleures performances
 *
 * @example
 * <shared-virtual-scroll
 *   [items]="myItems"
 *   [itemHeight]="60"
 *   [visibleItems]="10"
 *   [bufferSize]="3">
 *   <ng-template #itemTemplate let-item>
 *     <div class="list-item">{{ item.name }}</div>
 *   </ng-template>
 * </shared-virtual-scroll>
 */
@Component({
  selector: 'shared-virtual-scroll',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="virtual-scroll-container" #scrollContainer>
      <div class="virtual-scroll-spacer" [style.height.px]="totalHeight"></div>
      <div class="virtual-scroll-content" [style.transform]="'translateY(' + offsetY + 'px)'">
        <ng-container *ngFor="let item of visibleItemsData; trackBy: trackByFn">
          <ng-container
            *ngTemplateOutlet="itemTemplate; context: { $implicit: item, index: item.__index }"
          ></ng-container>
        </ng-container>
      </div>
    </div>
  `,
  styles: [
    `
      .virtual-scroll-container {
        position: relative;
        width: 100%;
        overflow-y: auto;
        overflow-x: hidden;
      }

      .virtual-scroll-spacer {
        position: absolute;
        top: 0;
        left: 0;
        width: 1px;
        pointer-events: none;
      }

      .virtual-scroll-content {
        will-change: transform;
      }
    `,
  ],
})
export class VirtualScrollComponent implements OnInit, AfterViewInit, OnDestroy {
  /** Liste complète des items */
  @Input() items: any[] = [];

  /** Template pour afficher chaque item */
  @Input() itemTemplate!: TemplateRef<any>;

  /** Hauteur de chaque item (px) */
  @Input() itemHeight = 50;

  /** Nombre d'items visibles à l'écran */
  @Input() visibleItems = 10;

  /** Taille du buffer (items rendus avant/après la zone visible) */
  @Input() bufferSize = 3;

  /** Hauteur du conteneur (si fixe) */
  @Input() containerHeight?: number;

  /** Événement quand on scroll près de la fin (infinite scroll) */
  @Output() nearEnd = new EventEmitter<void>();

  /** Seuil pour déclencher nearEnd (items restants) */
  @Input() nearEndThreshold = 5;

  @ViewChild('scrollContainer', { static: true })
  scrollContainer!: ElementRef<HTMLElement>;

  totalHeight = 0;
  offsetY = 0;
  visibleItemsData: any[] = [];

  private scrollTop = 0;
  private startIndex = 0;
  private endIndex = 0;

  ngOnInit(): void {
    this.calculateDimensions();
    this.updateVisibleItems();
  }

  ngAfterViewInit(): void {
    // Définir la hauteur du conteneur
    if (this.containerHeight) {
      this.scrollContainer.nativeElement.style.height = `${this.containerHeight}px`;
    } else {
      this.scrollContainer.nativeElement.style.height = `${
        this.visibleItems * this.itemHeight
      }px`;
    }
  }

  ngOnDestroy(): void {
    // Cleanup
  }

  @HostListener('scroll', ['$event'])
  onScroll(event: Event): void {
    const target = event.target as HTMLElement;
    this.scrollTop = target.scrollTop;

    this.updateVisibleItems();

    // Vérifier si on est près de la fin
    const scrollBottom = this.scrollTop + target.clientHeight;
    const nearEndPosition = this.totalHeight - this.nearEndThreshold * this.itemHeight;

    if (scrollBottom >= nearEndPosition) {
      this.nearEnd.emit();
    }
  }

  trackByFn(index: number, item: any): any {
    return item.__index ?? index;
  }

  private calculateDimensions(): void {
    this.totalHeight = this.items.length * this.itemHeight;
  }

  private updateVisibleItems(): void {
    // Calculer les indices de début et fin
    this.startIndex = Math.max(
      0,
      Math.floor(this.scrollTop / this.itemHeight) - this.bufferSize
    );

    this.endIndex = Math.min(
      this.items.length,
      Math.ceil((this.scrollTop + this.containerHeight!) / this.itemHeight) +
        this.bufferSize
    );

    // Extraire les items visibles
    this.visibleItemsData = this.items.slice(this.startIndex, this.endIndex).map((item, i) => ({
      ...item,
      __index: this.startIndex + i,
    }));

    // Calculer l'offset Y
    this.offsetY = this.startIndex * this.itemHeight;
  }

  /**
   * Scroller vers un index spécifique
   */
  scrollToIndex(index: number, behavior: ScrollBehavior = 'smooth'): void {
    const scrollTop = index * this.itemHeight;
    this.scrollContainer.nativeElement.scrollTo({ top: scrollTop, behavior });
  }

  /**
   * Rafraîchir les dimensions (appeler quand items change)
   */
  refresh(): void {
    this.calculateDimensions();
    this.updateVisibleItems();
  }
}
