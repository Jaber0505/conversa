import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'shared-input',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './input.component.html',
  styleUrls: ['./input.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => InputComponent),
      multi: true
    }
  ]
})
export class InputComponent implements ControlValueAccessor {
  @Input() id?: string;
  @Input() name?: string;
  @Input() label?: string;
  @Input() type: 'text' | 'email' | 'password' | 'number' = 'text';
  @Input() placeholder = '';
  @Input() disabled = false;

  // ✅ RESTAURE en @Input() pour autoriser [value]="..."
  @Input() set value(v: string | number | null | undefined) {
    this._value = (v ?? '').toString();
  }
  get value(): string { return this._value; }
  private _value = '';

  @Output() valueChange = new EventEmitter<string>();

  // CVA
  onChange = (_: string) => {};
  onTouched = () => {};

  writeValue(v: any): void {
    this._value = (v ?? '').toString();
  }
  registerOnChange(fn: any): void { this.onChange = fn; }
  registerOnTouched(fn: any): void { this.onTouched = fn; }
  setDisabledState(isDisabled: boolean) { this.disabled = isDisabled; }

  onInput(ev: Event) {
    const target = ev.target as HTMLInputElement;
    this._value = target.value;
    this.onChange(this._value);        // ngModel
    this.valueChange.emit(this._value); // [value]/(valueChange)
  }
}
