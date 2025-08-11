import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
    FormBuilder,
    FormGroup,
    Validators,
    ReactiveFormsModule,
    FormArray,
    AbstractControl
} from '@angular/forms';
import { TPipe } from '@app/core/i18n/t.pipe';
import { Router } from '@angular/router';

@Component({
    selector: 'app-register-page',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, TPipe],
    templateUrl: './register-page.component.html',
    styleUrls: ['./register-page.component.scss']
})
export class RegisterPageComponent {
    step = 1;
    maxSteps = 4;

    form: FormGroup;

    constructor(
        private fb: FormBuilder,
        private router: Router
    ) {
        this.form = this.fb.group({
            first_name: ['', Validators.required],
            last_name: ['', Validators.required],
            birth_date: ['', Validators.required],
            bio: ['', [Validators.required, Validators.minLength(20)]],
            language_native: ['', Validators.required],
            languages_spoken: this.fb.array([], Validators.required),
            languages_learning: this.fb.array([], Validators.required),
            email: ['', [Validators.required, Validators.email]],
            password: ['', [Validators.required, Validators.minLength(8)]],
            consent_given: [false, Validators.requiredTrue]
        });
    }

    get languagesSpoken(): FormArray {
        return this.form.get('languages_spoken') as FormArray;
    }

    get languagesLearning(): FormArray {
        return this.form.get('languages_learning') as FormArray;
    }

    addSpokenFromInput(ev: Event) {
        const input = ev.target as HTMLInputElement | null;
        const v = (input?.value ?? '').trim();
        if (!v) return;
        this.languagesSpoken.push(this.fb.control(v));
        if (input) input.value = '';
        this.languagesSpoken.markAsTouched();
    }

    removeSpokenAt(i: number) {
        this.languagesSpoken.removeAt(i);
        this.languagesSpoken.markAsTouched();
    }

    addLearningFromInput(ev: Event) {
        const input = ev.target as HTMLInputElement | null;
        const v = (input?.value ?? '').trim();
        if (!v) return;
        this.languagesLearning.push(this.fb.control(v));
        if (input) input.value = '';
        this.languagesLearning.markAsTouched();
    }

    removeLearningAt(i: number) {
        this.languagesLearning.removeAt(i);
        this.languagesLearning.markAsTouched();
    }

    nextStep() {
        if (this.isStepValid()) {
            this.step++;
        } else {
            this.form.markAllAsTouched();
        }
    }

    prevStep() {
        if (this.step > 1) this.step--;
    }

    isStepValid(): boolean {
        const stepControls = this.getStepControls();
        return stepControls.every(ctrl => ctrl?.valid);
    }

    private getStepControls(): AbstractControl[] {
        switch (this.step) {
            case 1:
                return [
                    this.form.get('first_name')!,
                    this.form.get('last_name')!,
                    this.form.get('birth_date')!
                ];
            case 2:
                return [this.form.get('bio')!];
            case 3:
                return [
                    this.form.get('language_native')!,
                    this.form.get('languages_spoken')!,
                    this.form.get('languages_learning')!
                ];
            case 4:
                return [
                    this.form.get('email')!,
                    this.form.get('password')!,
                    this.form.get('consent_given')!
                ];
            default:
                return [];
        }
    }

    getErrorKey(ctrlName: string): string {
        const ctrl = this.form.get(ctrlName);
        if (!ctrl || !ctrl.touched || !ctrl.errors) return '';
        if (ctrl.hasError('required')) return `errors.${ctrlName}_required`;
        if (ctrl.hasError('email')) return 'errors.email_invalid';
        if (ctrl.hasError('minlength')) return `errors.${ctrlName}_min_length`;
        if (ctrl.hasError('requiredTrue')) return 'errors.consent_required';
        return '';
    }

    submit() {
        if (this.form.valid) {
            console.log('Form data ready:', this.form.value);
            // Appel API d'inscription...
            this.router.navigate(['/fr']); // Redirection après inscription
        } else {
            this.form.markAllAsTouched();
        }
    }
}
