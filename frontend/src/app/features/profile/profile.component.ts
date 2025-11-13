import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { ContainerComponent, ButtonComponent, CardComponent } from '@shared';
import { TPipe } from '@core/i18n';
import { AuthApiService, AuthTokenService, type MeRes } from '@core/http';

@Component({
  standalone: true,
  selector: 'app-profile',
  imports: [
    CommonModule,
    FormsModule,
    ContainerComponent,
    ButtonComponent,
    CardComponent,
    TPipe
  ],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly tokens = inject(AuthTokenService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  lang = this.route.snapshot.paramMap.get('lang') ?? 'fr';

  user = signal<MeRes | null>(null);

  // Delete account modals
  showDeactivateModal = signal(false);
  showPermanentDeleteModal = signal(false);
  deletePassword = signal('');
  deleteError = signal<string | null>(null);
  deleteLoading = signal(false);
  deletionType = signal<'deactivate' | 'permanent'>('deactivate');

  ngOnInit() {
    // Load user data
    this.authApi.me().subscribe({
      next: (userData) => this.user.set(userData),
      error: (err) => console.error('Error loading user:', err)
    });
  }

  openDeactivateModal() {
    this.deletionType.set('deactivate');
    this.showDeactivateModal.set(true);
    this.deletePassword.set('');
    this.deleteError.set(null);
  }

  openPermanentDeleteModal() {
    this.deletionType.set('permanent');
    this.showPermanentDeleteModal.set(true);
    this.deletePassword.set('');
    this.deleteError.set(null);
  }

  closeDeleteModal() {
    this.showDeactivateModal.set(false);
    this.showPermanentDeleteModal.set(false);
    this.deletePassword.set('');
    this.deleteError.set(null);
  }

  confirmDeleteAccount() {
    const password = this.deletePassword();

    if (!password) {
      this.deleteError.set('PASSWORD_REQUIRED');
      return;
    }

    this.deleteLoading.set(true);
    this.deleteError.set(null);

    const deleteMethod = this.deletionType() === 'deactivate'
      ? this.authApi.deactivateAccount(password)
      : this.authApi.permanentlyDeleteAccount(password);

    deleteMethod.subscribe({
      next: () => {
        // Account deleted successfully
        this.deleteLoading.set(false);
        // Clear tokens and redirect to login
        this.tokens.clear();
        this.router.navigate(['/', this.lang, 'auth', 'login']);
      },
      error: (err) => {
        console.error('Delete account error:', err);
        this.deleteLoading.set(false);

        // Map backend error messages to translation keys
        const errorDetail = err?.error?.detail || '';
        let errorKey = 'PROFILE.DELETE_ACCOUNT_ERROR';

        if (errorDetail.includes('upcoming confirmed bookings')) {
          errorKey = 'PROFILE.CANNOT_DELETE_WITH_BOOKINGS';
        } else if (errorDetail.includes('organizing upcoming published events')) {
          errorKey = 'PROFILE.CANNOT_DELETE_WITH_EVENTS';
        } else if (errorDetail.includes('Invalid password')) {
          errorKey = 'auth.errors.bad_credentials';
        }

        this.deleteError.set(errorKey);
      }
    });
  }

  goBack() {
    this.router.navigate(['/', this.lang, 'events']);
  }

  get userEmail(): string {
    return this.user()?.email || '';
  }

  get userFullName(): string {
    const u = this.user();
    if (!u) return '';
    return `${u.first_name} ${u.last_name}`;
  }

  get userAge(): number {
    return this.user()?.age || 0;
  }

  get userJoinedDate(): string {
    // date_joined is not available in MeRes API response
    // We can remove this or fetch from a different endpoint if needed
    return '-';
  }

  get nativeLanguages(): string {
    const langs = this.user()?.native_langs || [];
    if (langs.length === 0) return '-';

    return langs.map((lang: any) => {
      const key = `label_${this.lang}` as keyof typeof lang;
      return lang[key] || lang.label_en;
    }).join(', ');
  }

  get targetLanguages(): string {
    const langs = this.user()?.target_langs || [];
    if (langs.length === 0) return '-';

    return langs.map((lang: any) => {
      const key = `label_${this.lang}` as keyof typeof lang;
      return lang[key] || lang.label_en;
    }).join(', ');
  }
}
