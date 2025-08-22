// blocking-spinner.component.ts
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, HostListener, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import {BlockingSpinnerService} from "@app/core/http/services/spinner-service";

@Component({
  selector: 'ui-blocking-spinner',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ui-spinner.html',
  styleUrls: ['./ui-spinner.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BlockingSpinnerComponent implements OnDestroy {
  private svc = inject(BlockingSpinnerService);
  private cdr = inject(ChangeDetectorRef);      // ✅
  private sub = new Subscription();
  show = false;
  message?: string;

  constructor() {
    this.sub.add(
      this.svc.state$.subscribe(s => {
        this.show = s.show;
        this.message = s.message;
        if (s.show) setTimeout(() => this.focusTrap(), 0);
        this.cdr.markForCheck();                // ✅ force la maj OnPush
      })
    );
  }
  ngOnDestroy() { this.sub.unsubscribe(); }

  @HostListener('document:keydown', ['$event'])
  onKeydown(e: KeyboardEvent) {
    if (!this.show) return;
    if (e.key === 'Escape' || e.key === 'Tab') e.preventDefault();
  }
  @HostListener('document:focusin') onFocusIn() { if (this.show) this.focusTrap(); }
  private focusTrap() { document.getElementById('blocking-modal')?.focus(); }
}
