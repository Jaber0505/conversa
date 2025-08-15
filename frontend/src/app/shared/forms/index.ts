import { FormFieldComponent } from './form-field/form-field.component';
import { InputComponent }     from './input/input.component';
import { SelectComponent }    from './select/select.component';
import { SearchBarComponent } from './search-bar/search-bar.component';
import { MultiSelectComponent } from './multi-select/multi-select.component';

export { FormFieldComponent } from './form-field/form-field.component';
export { InputComponent }     from './input/input.component';
export { SelectComponent }    from './select/select.component';
export { SearchBarComponent } from './search-bar/search-bar.component';
export { MultiSelectComponent } from './multi-select/multi-select.component';

export const SHARED_FORMS = [ FormFieldComponent, InputComponent, SelectComponent, SearchBarComponent, MultiSelectComponent ] as const;
