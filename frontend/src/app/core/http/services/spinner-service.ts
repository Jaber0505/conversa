import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type BlockingState = { show: boolean; message?: string };

@Injectable({ providedIn: 'root' })
export class BlockingSpinnerService {
  private _state = new BehaviorSubject<BlockingState>({ show: false });
  readonly state$ = this._state.asObservable();

  show(message?: string) {
    this._state.next({ show: true, message });
    document.body.style.overflow = 'hidden';
  }
  hide() {
    this._state.next({ show: false });
    document.body.style.overflow = '';
  }
}
